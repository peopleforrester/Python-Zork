#!/usr/bin/env python3
"""
ABOUTME: Unit tests for server.py helpers — env-var parsing and config.
ABOUTME: Imports server module without starting Flask.
"""

import unittest
import unittest.mock

import server


class TestParseOrigins(unittest.TestCase):
    """server._parse_origins must turn an env string into a clean list."""

    def test_default_when_unset(self):
        self.assertEqual(server._parse_origins(None), ["http://localhost:5173"])

    def test_default_when_empty(self):
        self.assertEqual(server._parse_origins(""), ["http://localhost:5173"])

    def test_single_origin(self):
        self.assertEqual(
            server._parse_origins("https://example.com"),
            ["https://example.com"],
        )

    def test_comma_separated(self):
        self.assertEqual(
            server._parse_origins("https://a.com,https://b.com"),
            ["https://a.com", "https://b.com"],
        )

    def test_strips_whitespace_and_drops_blanks(self):
        self.assertEqual(
            server._parse_origins("  https://a.com ,, https://b.com  ,"),
            ["https://a.com", "https://b.com"],
        )


class TestEnvFlags(unittest.TestCase):
    """Boolean env helpers default safe (debug off, localhost host)."""

    def test_debug_default_off(self):
        self.assertFalse(server._env_bool(None))
        self.assertFalse(server._env_bool(""))
        self.assertFalse(server._env_bool("0"))
        self.assertFalse(server._env_bool("false"))

    def test_debug_on_when_truthy(self):
        self.assertTrue(server._env_bool("1"))
        self.assertTrue(server._env_bool("true"))
        self.assertTrue(server._env_bool("yes"))


class TestSocketHandlers(unittest.TestCase):
    """End-to-end test of the Socket.IO handlers via flask_socketio's
    test client. Verifies the in-process Game runs and snapshots flow back
    over the wire — no PTY, no subprocess."""

    def setUp(self):
        # Clear any leftover session state between tests.
        server._sessions.clear()
        server._input_buffers.clear()
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()
        server._input_buffers.clear()

    def _send_line(self, text):
        """Helper: type a full command line including the trailing Enter."""
        self.client.emit("terminal_input", {"input": text + "\r"})

    def _received_by_event(self, event_name):
        return [m for m in self.client.get_received() if m["name"] == event_name]

    def test_start_game_creates_session_and_emits_welcome(self):
        self.client.emit("start_game")
        events = self.client.get_received()
        names = [e["name"] for e in events]

        self.assertIn("game_started", names)
        self.assertIn("terminal_output", names)
        self.assertIn("game_state", names)

        # The welcome text contains the project name.
        terminal = next(e for e in events if e["name"] == "terminal_output")
        self.assertIn("KodeKloud", terminal["args"][0]["output"])

        # One session per connected client.
        self.assertEqual(len(server._sessions), 1)

    def test_terminal_input_runs_command_and_emits_snapshot(self):
        self.client.emit("start_game")
        self.client.get_received()  # drain

        self._send_line("look")
        events = self.client.get_received()
        names = [e["name"] for e in events]

        self.assertIn("terminal_output", names)
        self.assertIn("game_state", names)

        snapshot = next(e for e in events if e["name"] == "game_state")["args"][0]
        self.assertIn("player", snapshot)
        self.assertIn("rooms", snapshot)

    def test_keystrokes_buffer_until_newline(self):
        self.client.emit("start_game")
        self.client.get_received()  # drain

        # Type three characters separately — should echo but not flush.
        self.client.emit("terminal_input", {"input": "l"})
        self.client.emit("terminal_input", {"input": "o"})
        self.client.emit("terminal_input", {"input": "o"})

        events = self.client.get_received()
        # Only echo events; no game_state yet because no Enter.
        names = [e["name"] for e in events]
        self.assertNotIn("game_state", names)
        self.assertTrue(all(e["name"] == "terminal_output" for e in events))

        # Now send 'k' + Enter: buffer flushes as 'look'.
        self.client.emit("terminal_input", {"input": "k\r"})
        events = self.client.get_received()
        self.assertIn("game_state", [e["name"] for e in events])

    def test_backspace_erases_buffered_character(self):
        self.client.emit("start_game")
        self.client.get_received()

        # Type 'lookx', backspace, Enter: buffer should be 'look'.
        self.client.emit("terminal_input", {"input": "lookx"})
        self.client.emit("terminal_input", {"input": "\x7f"})
        self.client.emit("terminal_input", {"input": "\r"})
        events = self.client.get_received()
        # If the backspace worked, the command was 'look' which is read-only
        # and the snapshot's turn counter should still be 0.
        snapshot = next(e for e in events if e["name"] == "game_state")["args"][0]
        self.assertEqual(snapshot["turn"], 0)

    def test_query_state_re_emits_snapshot(self):
        self.client.emit("start_game")
        self.client.get_received()  # drain

        self.client.emit("query_state")
        events = self.client.get_received()
        snapshots = [e for e in events if e["name"] == "game_state"]

        self.assertEqual(len(snapshots), 1)
        self.assertIn("rooms", snapshots[0]["args"][0])

    def test_input_with_no_active_game_returns_helpful_message(self):
        # No start_game called.
        self.client.emit("terminal_input", {"input": "look\r"})
        events = self.client.get_received()
        terminal = next((e for e in events if e["name"] == "terminal_output"), None)
        self.assertIsNotNone(terminal)
        self.assertIn("no active game", terminal["args"][0]["output"])

    def test_quit_verb_is_intercepted_and_does_not_block(self):
        self.client.emit("start_game")
        self.client.get_received()  # drain

        # If the server forwarded 'quit' to game.feed(), QuitCommand would
        # call input() and block. Intercepting it short-circuits to a
        # helpful message instead.
        self._send_line("quit")
        events = self.client.get_received()
        outputs = [e["args"][0]["output"] for e in events if e["name"] == "terminal_output"]
        self.assertTrue(any("close the browser tab" in o for o in outputs))


if __name__ == "__main__":
    unittest.main()


class TestFeedCrashSafety(unittest.TestCase):
    """A crash inside Game.feed must surface in the terminal, not vanish."""

    def test_handle_line_reports_internal_errors(self) -> None:
        import server as server_module

        emitted = []

        class ExplodingGame:
            def feed(self, line):
                raise RuntimeError("boom")

        with unittest.mock.patch.object(
            server_module, "emit", lambda *a, **k: emitted.append(a)
        ):
            server_module._handle_line("sid-x", ExplodingGame(), "knowledge")

        text = " ".join(str(a) for a in emitted)
        self.assertIn("internal error", text.lower())
