#!/usr/bin/env python3
"""
ABOUTME: Unit tests for server.py helpers — env-var parsing and config.
ABOUTME: Imports server module without starting Flask.
"""

import unittest

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
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()

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

        self.client.emit("terminal_input", {"input": "look"})
        events = self.client.get_received()
        names = [e["name"] for e in events]

        self.assertIn("terminal_output", names)
        self.assertIn("game_state", names)

        snapshot = next(e for e in events if e["name"] == "game_state")["args"][0]
        self.assertIn("player", snapshot)
        self.assertIn("rooms", snapshot)

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
        self.client.emit("terminal_input", {"input": "look"})
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
        self.client.emit("terminal_input", {"input": "quit"})
        events = self.client.get_received()
        terminal = next(e for e in events if e["name"] == "terminal_output")
        self.assertIn("close the browser tab", terminal["args"][0]["output"])


if __name__ == "__main__":
    unittest.main()
