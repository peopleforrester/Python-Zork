# ABOUTME: Flask + Socket.IO front-end that runs Game in-process and
# ABOUTME: exposes a per-session terminal + structured snapshot. Dev-only.

import logging
import os

from flask import Flask, jsonify, request, send_from_directory
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


def _resolve_host(cq_host, has_port):
    """Resolve the bind address.

    An explicit CQ_HOST always wins. Otherwise bind 0.0.0.0 when a platform
    PORT is injected (Railway and most PaaS), since their edge proxy reaches the
    container over its network interface, not loopback; fall back to loopback
    for local dev so the dev server is not exposed on the LAN.
    """
    if cq_host:
        return cq_host
    return "0.0.0.0" if has_port else "127.0.0.1"


def _socket_origins(serving_dist, cors_origins):
    """Allowed Socket.IO handshake origins.

    When the bundled dist/ is served (single-service production), the page and
    socket share an origin that is the platform domain, unknown at build time,
    so accept any origin for the handshake. In dev the page is served by Vite on
    a known localhost port, so keep the explicit allowlist.
    """
    return "*" if serving_dist else cors_origins


def _clamp_input(raw, limit):
    """Truncate an oversized single input event.

    Guards against a paste-bomb / echo-amplification event on the public,
    unauthenticated socket: one giant string would otherwise be buffered and
    echoed character by character.
    """
    return raw[:limit] if len(raw) > limit else raw


# --- Configuration from environment -----------------------------------------

# Longest single terminal_input event we accept, and the longest line we buffer
# before dropping further keystrokes. Generous for real typing/pastes, small
# enough to bound memory and echo work per event.
MAX_INPUT_EVENT = 4096
MAX_LINE = 1024

CORS_ORIGINS = _parse_origins(os.environ.get("CQ_CORS_ORIGINS"))
DEBUG = _env_bool(os.environ.get("CQ_DEBUG"))
HOST = _resolve_host(os.environ.get("CQ_HOST"), "PORT" in os.environ)
PORT = int(os.environ.get("CQ_PORT") or os.environ.get("PORT") or "5000")

# Directory of the built frontend. When present we are in single-service mode
# (Flask serves the page and the socket same-origin); when absent, dev mode.
_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
_SERVING_DIST = os.path.isdir(_DIST)


# --- App ---------------------------------------------------------------------

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)
socketio = SocketIO(app, cors_allowed_origins=_socket_origins(_SERVING_DIST, CORS_ORIGINS))

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


def _deploy_commit(env=None):
    """The commit this process is serving, or 'unknown'.

    Read from DEPLOY_SHA, which scripts/deploy.py sets on the service before
    uploading, falling back to the platform-injected RAILWAY_GIT_COMMIT_SHA.
    Without this a deploy cannot be confirmed from outside: the platform
    reporting "Online" only means the service is up on its last successful
    build, which may predate the commit you just pushed.

    A file-based stamp was tried first and does not work here, because the
    uploader honours .gitignore and an ignored stamp never reaches the image.
    """
    env = os.environ if env is None else env
    for key in ("DEPLOY_SHA", "RAILWAY_GIT_COMMIT_SHA"):
        value = (env.get(key) or "").strip()
        if value:
            return value
    return "unknown"


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "commit": _deploy_commit()})


# Serve the built frontend when dist/ exists (Railway single-service mode:
# same origin for page + socket, so no CORS in production). Local dev keeps
# using the Vite server on :5173 and this route 404s harmlessly.


@app.route("/")
def index():
    if os.path.isdir(_DIST):
        return send_from_directory(_DIST, "index.html")
    return jsonify({"error": "frontend not built; run npm run build"}), 404


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(_DIST, "assets"), filename)


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


def _resolve_verb(game: Game, line: str) -> str:
    """Resolve the first token of a line through the game's prefix matcher.

    Game.feed() accepts abbreviations (``qui`` -> ``quit``), so the server must
    resolve the same way before deciding whether to intercept an exit verb;
    otherwise an abbreviated ``quit`` slips through to QuitCommand, which blocks
    on input() with no client stdin.
    """
    token = line.strip().split(" ", 1)[0].lower() if line.strip() else ""
    if not token:
        return ""
    return game._match_command_prefix(token)


def _handle_line(sid: str, game: Game, line: str) -> None:
    """Feed one whole command line to the game and emit the result."""
    verb = _resolve_verb(game, line)

    if verb in _INTERCEPTED_VERBS:
        emit("terminal_output", {"output": "\n\r[server] close the browser tab to exit.\n\r> "})
        return

    try:
        response = game.feed(line)
    except Exception:
        # A crash must surface in the player's terminal, not vanish into
        # a swallowed handler exception with a hung prompt.
        logger.exception("feed crashed for %s on line %r", sid, line)
        emit(
            "terminal_output",
            {"output": "\n\r[server] internal error running that command.\n\r> "},
        )
        return
    if response:
        emit("terminal_output", {"output": f"\n\r{response}\n\r"})

    logger.info("line handled for %s: %r -> turn=%d", sid, line, game.turns)
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
    raw = _clamp_input(raw, MAX_INPUT_EVENT)

    buf = _input_buffers.get(sid, "")
    # Coalesce echoes into one emit per event instead of one per character, so a
    # multi-character (pasted) event cannot amplify into a flood of socket sends.
    echo: list[str] = []

    def flush_echo() -> None:
        if echo:
            emit("terminal_output", {"output": "".join(echo)})
            echo.clear()

    for char in raw:
        if char in ("\r", "\n"):
            # Echo a newline so the terminal advances, then flush the line.
            echo.append("\n\r")
            flush_echo()
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
                echo.append("\b \b")
        elif char == "\x03":
            # Ctrl-C: abandon the current line.
            buf = ""
            echo.append("^C\n\r> ")
        elif char >= " " and char != "\x7f":
            # Printable. Append and echo, unless the line is already at the cap.
            if len(buf) < MAX_LINE:
                buf += char
                echo.append(char)
        # Drop anything else (escape sequences, arrow keys, tab — out of scope).

    flush_echo()
    _input_buffers[sid] = buf


@socketio.on("query_state")
def handle_query_state():
    """Re-send the current snapshot. Used when the React map first mounts."""
    sid = _session_id()
    game = _get_game(sid) if sid else None
    if game is None:
        logger.info("query_state from %s: no session", sid)
        return
    logger.info("query_state from %s: turn=%d", sid, game.turns)
    emit("game_state", game.snapshot())


if __name__ == "__main__":
    logger.info("Starting on %s:%d (debug=%s, origins=%s)", HOST, PORT, DEBUG, CORS_ORIGINS)
    # allow_unsafe_werkzeug: flask-socketio hard-errors on the Werkzeug dev
    # server when debug is off. This server is documented dev-only (see
    # README security caveat), so the opt-in is deliberate.
    socketio.run(app, debug=DEBUG, port=PORT, host=HOST, allow_unsafe_werkzeug=True)
