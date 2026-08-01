#!/usr/bin/env python3
"""
ABOUTME: Tab completion for the web terminal and per-command help.
ABOUTME: Candidates come from the server so there is one source of truth.
"""

import unittest

import server
from tests._helpers import build_real_game


class TestCompletionCandidates(unittest.TestCase):
    """The CLI has had a readline completer all along; it is unreachable from
    the browser, which is where the game is actually played."""

    def setUp(self):
        self.game = build_real_game()

    def _complete(self, line):
        return self.game.completions(line)

    def test_empty_input_offers_commands(self):
        self.assertIn("look", self._complete(""))

    def test_a_command_prefix_narrows(self):
        out = self._complete("sc")
        self.assertIn("scan", out)
        self.assertNotIn("look", out)

    def test_directions_complete(self):
        self.assertTrue(any(d.startswith("nor") for d in self._complete("nor")))

    def test_take_offers_only_room_items(self):
        """The readline completer already special-cased this; keep it."""
        room = self.game.player.location
        room.items["widget_here"] = "in the room"
        self.game.player.items["widget_held"] = "in the pack"
        out = self._complete("take widget")
        self.assertIn("widget_here", out)
        self.assertNotIn("widget_held", out)

    def test_drop_offers_only_inventory_items(self):
        room = self.game.player.location
        room.items["widget_here"] = "in the room"
        self.game.player.items["widget_held"] = "in the pack"
        out = self._complete("drop widget")
        self.assertIn("widget_held", out)
        self.assertNotIn("widget_here", out)

    def test_solve_offers_puzzle_ids_for_this_room(self):
        self.game.feed("n")  # Core 1 has a puzzle
        out = self._complete("solve ")
        self.assertTrue(out)
        for pid in out:
            self.assertIn(pid, self.game.player.location.puzzles)

    def test_unknown_prefix_returns_nothing_rather_than_everything(self):
        self.assertEqual(self._complete("zzzz"), [])

    def test_results_are_sorted_and_unique(self):
        out = self._complete("s")
        self.assertEqual(out, sorted(set(out)))


class TestPerCommandHelp(unittest.TestCase):
    """`help scan` used to dump all 70+ lines, because the argument was ignored."""

    def setUp(self):
        self.game = build_real_game()

    def test_bare_help_still_shows_the_full_screen(self):
        self.assertGreater(len(self.game.feed("help").splitlines()), 40)

    def test_help_for_a_command_is_short_and_specific(self):
        out = self.game.feed("help scan")
        self.assertLess(len(out.splitlines()), 12)
        self.assertIn("scan", out.lower())

    def test_every_registered_command_has_an_entry(self):
        for name in self.game.command_processor.commands:
            with self.subTest(command=name):
                out = self.game.feed(f"help {name}")
                self.assertTrue(out.strip())
                self.assertNotIn("Unknown", out)

    def test_an_unknown_command_suggests_near_matches(self):
        out = self.game.feed("help scn")
        self.assertIn("scan", out)

    def test_help_is_read_only(self):
        before = self.game.turns
        self.game.feed("help scan")
        self.assertEqual(self.game.turns, before)


class TestCompletionOverTheSocket(unittest.TestCase):
    def setUp(self):
        server._sessions.clear()
        server._input_buffers.clear()
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()

    def test_server_answers_a_completion_request(self):
        self.client.emit("start_game")
        self.client.get_received()
        self.client.emit("complete", {"line": "sc"})
        events = [m for m in self.client.get_received() if m["name"] == "completions"]
        self.assertTrue(events)
        self.assertIn("scan", events[0]["args"][0]["matches"])

    def test_completion_before_a_game_is_harmless(self):
        self.client.emit("complete", {"line": "sc"})
        self.assertTrue(True)  # must not raise

    def test_malformed_completion_payload_is_ignored(self):
        self.client.emit("start_game")
        self.client.get_received()
        for payload in (None, "sc", 42, {}):
            self.client.emit("complete", payload)
        self.assertTrue(True)  # must not raise


if __name__ == "__main__":
    unittest.main()
