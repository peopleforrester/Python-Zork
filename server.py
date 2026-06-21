# ABOUTME: Flask + Socket.IO front-end that runs Game in-process and
# ABOUTME: exposes a per-session terminal + structured snapshot. Dev-only.

import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from computerquest.game import Game

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

# Per-session Game instances. Keyed by Socket.IO session id. Single-user dev
# server, but the keying keeps state isolated if multiple browser tabs connect.
_sessions: dict[str, Game] = {}

# Per-session input buffer. The browser's xterm.js sends every keystroke as a
# separate terminal_input event; we accumulate until newline, then flush a
# whole line into Game.feed.
_input_buffers: dict[str, str] = {}

# Verbs the server intercepts before they reach Game.feed(), because the
# CLI implementations block on input(). The web UI handles its own session
# lifecycle (disconnect/refresh) so we never need the synchronous prompt.
_INTERCEPTED_VERBS = frozenset({"quit", "exit", "q"})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


def _session_id() -> str | None:
    """Resolve the current Socket.IO session id from the request context."""
    return getattr(request, "sid", None)


def _get_game(sid: str) -> Game | None:
    return _sessions.get(sid)


@socketio.on("connect")
def handle_connect():
    sid = _session_id()
    logger.info("Client connected: %s", sid)


@socketio.on("disconnect")
def handle_disconnect():
    sid = _session_id()
    if sid:
        _sessions.pop(sid, None)
        _input_buffers.pop(sid, None)
    logger.info("Client disconnected: %s", sid)


@socketio.on("start_game")
def start_game():
    """Create a fresh Game for this session and send the welcome + snapshot."""
    sid = _session_id()
    if sid is None:
        return

    game = Game()
    _sessions[sid] = game
    _input_buffers[sid] = ""

    emit("game_started")
    emit("terminal_output", {"output": game.welcome_text()})
    emit("terminal_output", {"output": "\n\r> "})
    emit("game_state", game.snapshot())


def _handle_line(sid: str, game: Game, line: str) -> None:
    """Feed one whole command line to the game and emit the result."""
    verb = line.strip().split(" ", 1)[0].lower() if line.strip() else ""

    if verb in _INTERCEPTED_VERBS:
        emit("terminal_output", {"output": "\n\r[server] close the browser tab to exit.\n\r> "})
        return

    response = game.feed(line)
    if response:
        emit("terminal_output", {"output": f"\n\r{response}\n\r"})

    emit("game_state", game.snapshot())

    if game.game_over:
        emit("game_ended", {"victory": game.victory})
    else:
        emit("terminal_output", {"output": "\n\r> "})


@socketio.on("terminal_input")
def handle_input(data):
    """Buffer keystrokes per session; flush a line on Enter.

    xterm.js sends every keystroke as a separate event. We accumulate them
    server-side and call game.feed() once a complete line arrives.
    """
    sid = _session_id()
    game = _get_game(sid) if sid else None
    if game is None or sid is None:
        emit("terminal_output", {"output": "[server] no active game; click Start Game.\n\r"})
        return

    raw = data.get("input", "") if isinstance(data, dict) else ""
    if not raw:
        return

    buf = _input_buffers.get(sid, "")

    for char in raw:
        if char in ("\r", "\n"):
            # Echo a newline so the terminal advances, then flush.
            emit("terminal_output", {"output": "\n\r"})
            line, buf = buf, ""
            _input_buffers[sid] = buf
            _handle_line(sid, game, line)
            game = _get_game(sid)
            if game is None:
                return
        elif char in ("\x7f", "\b"):
            # Backspace: drop one char from the buffer and erase visually.
            if buf:
                buf = buf[:-1]
                emit("terminal_output", {"output": "\b \b"})
        elif char == "\x03":
            # Ctrl-C: abandon the current line.
            buf = ""
            emit("terminal_output", {"output": "^C\n\r> "})
        elif char >= " " and char != "\x7f":
            # Printable. Append and echo.
            buf += char
            emit("terminal_output", {"output": char})
        # Drop anything else (escape sequences, arrow keys, tab — out of scope).

    _input_buffers[sid] = buf


@socketio.on("query_state")
def handle_query_state():
    """Re-send the current snapshot. Used when the React map first mounts."""
    sid = _session_id()
    game = _get_game(sid) if sid else None
    if game is None:
        return
    emit("game_state", game.snapshot())


if __name__ == "__main__":
    logger.info("Starting on %s:%d (debug=%s, origins=%s)", HOST, PORT, DEBUG, CORS_ORIGINS)
    socketio.run(app, debug=DEBUG, port=PORT, host=HOST)
