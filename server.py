# ABOUTME: Flask + Socket.IO front-end that pipes a forked Python-Zork
# ABOUTME: process to xterm.js in the browser. Dev-only — see README.

import atexit
import fcntl
import logging
import os
import select
import signal
import struct
import subprocess
import sys
import termios

import pty

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

logger = logging.getLogger("python_zork.server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# --- Env parsing helpers (importable, testable) -----------------------------

_DEFAULT_ORIGINS = ["http://localhost:5173"]


def _parse_origins(env_value):
    """Parse comma-separated CORS origins from env into a clean list.

    Returns the dev default when env is unset or empty.
    """
    if not env_value:
        return list(_DEFAULT_ORIGINS)
    return [o.strip() for o in env_value.split(",") if o.strip()]


def _env_bool(env_value):
    """True iff env_value is a truthy string ('1', 'true', 'yes', case-insensitive)."""
    if not env_value:
        return False
    return env_value.strip().lower() in {"1", "true", "yes", "on"}


# --- Configuration from environment -----------------------------------------

CORS_ORIGINS = _parse_origins(os.environ.get("CQ_CORS_ORIGINS"))
DEBUG = _env_bool(os.environ.get("CQ_DEBUG"))
HOST = os.environ.get("CQ_HOST", "127.0.0.1")
PORT = int(os.environ.get("CQ_PORT", "5000"))


# --- App ---------------------------------------------------------------------

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)
socketio = SocketIO(app, cors_allowed_origins=CORS_ORIGINS)

# Per-session state. Multiple clients are not supported — the last connection wins.
game_fd = None
game_process = None


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


def _terminate_game_process():
    """Send SIGTERM to the spawned game process if it's still running."""
    global game_process, game_fd
    if game_process is None:
        return
    try:
        os.kill(game_process.pid, signal.SIGTERM)
        game_process.wait(timeout=2)
    except ProcessLookupError:
        # Process already exited — nothing to clean up.
        pass
    except subprocess.TimeoutExpired:
        logger.warning("Game process %s did not exit in time; sending SIGKILL", game_process.pid)
        try:
            os.kill(game_process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except OSError as exc:
        logger.warning("Failed to terminate game process %s: %s", game_process.pid, exc)
    finally:
        game_process = None
        if game_fd is not None:
            try:
                os.close(game_fd)
            except OSError:
                pass
            game_fd = None


# Best-effort cleanup if the server itself shuts down with a child still alive.
atexit.register(_terminate_game_process)


@socketio.on("connect")
def handle_connect():
    logger.info("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected")
    _terminate_game_process()


@socketio.on("terminal_input")
def handle_input(data):
    if game_fd is not None:
        os.write(game_fd, data["input"].encode())


@socketio.on("resize")
def handle_resize(data):
    if game_fd is None:
        return
    rows, cols = data["rows"], data["cols"]
    try:
        fcntl.ioctl(game_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    except OSError as exc:
        logger.warning("Error resizing terminal: %s", exc)


@socketio.on("start_game")
def start_game():
    global game_fd, game_process

    # Replace any existing game process before starting a new one.
    _terminate_game_process()

    game_fd, slave_fd = pty.openpty()
    game_process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        start_new_session=True,
    )

    os.close(slave_fd)
    fcntl.fcntl(game_fd, fcntl.F_SETFL, os.O_NONBLOCK)

    emit("game_started")
    socketio.start_background_task(read_output)


def read_output():
    global game_fd, game_process
    max_read_bytes = 1024 * 20

    while game_process and game_process.poll() is None:
        try:
            r, _w, _e = select.select([game_fd], [], [], 0.1)
            if r:
                output = os.read(game_fd, max_read_bytes).decode(errors="ignore")
                if output:
                    socketio.emit("terminal_output", {"output": output})
        except (OSError, IOError) as exc:
            logger.warning("Error reading from terminal: %s", exc)
            break

    if game_process and game_process.poll() is not None:
        socketio.emit("game_ended", {"exit_code": game_process.returncode})


if __name__ == "__main__":
    logger.info("Starting on %s:%d (debug=%s, origins=%s)", HOST, PORT, DEBUG, CORS_ORIGINS)
    socketio.run(app, debug=DEBUG, port=PORT, host=HOST)
