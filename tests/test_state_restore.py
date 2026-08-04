#!/usr/bin/env python3
"""
ABOUTME: A browser refresh resumes the game from the blob the client kept.
ABOUTME: The blob is client-supplied, so a bad one must never half-apply.
"""

import unittest

import server
from tests._helpers import build_real_game


class TestStateBlobIsPushed(unittest.TestCase):
    """The browser can only resume what the server told it about."""

    def setUp(self):
        for store in (server._sessions, server._input_buffers, server._save_scopes):
            store.clear()
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()

    def _blobs(self):
        return [m["args"][0] for m in self.client.get_received() if m["name"] == "state_blob"]

    def test_starting_a_game_pushes_a_blob(self):
        self.client.emit("start_game")
        self.assertTrue(self._blobs())

    def test_the_blob_is_a_loadable_save(self):
        self.client.emit("start_game")
        blob = self._blobs()[-1]
        for key in ("version", "turns", "player", "components", "game_state"):
            with self.subTest(key=key):
                self.assertIn(key, blob)

    def test_playing_pushes_an_updated_blob(self):
        self.client.emit("start_game")
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "n\r"})
        blobs = self._blobs()
        self.assertTrue(blobs)
        self.assertGreater(blobs[-1]["turns"], 0)


class TestRefreshResumes(unittest.TestCase):
    """The behaviour the player actually notices."""

    def setUp(self):
        for store in (server._sessions, server._input_buffers, server._save_scopes):
            store.clear()

    def tearDown(self):
        server._sessions.clear()

    def _play_then_reconnect(self, commands):
        first = server.socketio.test_client(server.app)
        first.emit("start_game", {"save_key": "browser-a"})
        for c in commands:
            first.emit("terminal_input", {"input": c + "\r"})
        blob = [m["args"][0] for m in first.get_received() if m["name"] == "state_blob"][-1]
        first.disconnect()

        second = server.socketio.test_client(server.app)   # the refresh
        second.emit("start_game", {"save_key": "browser-a", "restore": blob})
        game = next(iter(server._sessions.values()))
        return second, game, blob

    def test_the_turn_count_survives(self):
        _, game, blob = self._play_then_reconnect(["n", "s", "n"])
        self.assertEqual(game.turns, blob["turns"])
        self.assertGreater(game.turns, 0)

    def test_the_player_is_back_where_they_were(self):
        _, game, blob = self._play_then_reconnect(["n"])
        self.assertEqual(game.player.location.id, blob["player"]["location"])

    def test_solved_puzzles_survive(self):
        client, game, _ = self._play_then_reconnect(
            ["n", "solve pipeline_forwarding_intro", "answer 8"]
        )
        self.assertIn("pipeline_forwarding_intro", game.player.solved_puzzles)
        client.disconnect()

    def test_the_player_is_told_they_resumed(self):
        client, _, _ = self._play_then_reconnect(["n"])
        text = " ".join(
            str(m["args"][0].get("output", ""))
            for m in client.get_received() if m["name"] == "terminal_output"
        )
        self.assertIn("resumed", text.lower())
        client.disconnect()

    def test_starting_without_a_blob_is_a_fresh_game(self):
        client = server.socketio.test_client(server.app)
        client.emit("start_game", {"save_key": "browser-b"})
        game = next(iter(server._sessions.values()))
        self.assertEqual(game.turns, 0)
        client.disconnect()


class TestABadBlobIsRefusedSafely(unittest.TestCase):
    """The blob comes from the browser, so it is untrusted input."""

    def setUp(self):
        for store in (server._sessions, server._input_buffers, server._save_scopes):
            store.clear()
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()

    def _start_with(self, blob):
        self.client.emit("start_game", {"save_key": "k", "restore": blob})
        return next(iter(server._sessions.values()))

    def test_garbage_starts_a_fresh_game_rather_than_crashing(self):
        for blob in ({}, {"turns": "not a number"}, {"player": {}}, {"components": 5}):
            with self.subTest(blob=blob):
                game = self._start_with(blob)
                self.assertIsNotNone(game)

    def test_a_non_object_is_ignored(self):
        for blob in ("a string", 42, [1, 2], None):
            with self.subTest(blob=blob):
                game = self._start_with(blob)
                self.assertEqual(game.turns, 0)

    def test_an_unknown_room_leaves_the_player_somewhere_real(self):
        good = build_real_game().save_load._serialize("x")
        good["player"]["location"] = "NOWHERE"
        game = self._start_with(good)
        self.assertIn(game.player.location, game.game_map.rooms.values())

    def test_a_partially_valid_blob_does_not_half_apply(self):
        """_apply validates everything before it writes anything, so a blob
        that fails late must leave the fresh game untouched."""
        good = build_real_game().save_load._serialize("x")
        good["player"]["health"] = 3
        del good["components"]
        game = self._start_with(good)
        self.assertNotEqual(game.player.health, 3)


if __name__ == "__main__":
    unittest.main()
