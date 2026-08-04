#!/usr/bin/env python3
"""
ABOUTME: Saves are scoped per client so two players cannot collide or peek.
ABOUTME: The scope key comes from the browser, so it is hashed, never used raw.
"""

import tempfile
import unittest
from pathlib import Path

import server
from computerquest.mechanics.save_load import SaveLoadSystem
from tests._helpers import build_real_game


class TestScopeKeyIsSafe(unittest.TestCase):
    """The key arrives from the browser and becomes a directory name, so it is
    the one untrusted value in this feature."""

    def test_a_key_becomes_a_hex_digest(self):
        scope = server._save_scope("player-one")
        self.assertRegex(scope, r"^[0-9a-f]{16}$")

    def test_the_same_key_always_gives_the_same_scope(self):
        """A refresh keeps the browser's key, and that is what makes `load`
        still work afterwards."""
        self.assertEqual(server._save_scope("abc"), server._save_scope("abc"))

    def test_different_keys_give_different_scopes(self):
        self.assertNotEqual(server._save_scope("abc"), server._save_scope("abd"))

    def test_path_traversal_cannot_escape(self):
        """Hashing means no input can walk the filesystem, whatever it holds."""
        for evil in ("../../etc/passwd", "/etc/passwd", "..", ".", "a/b/c",
                     "\x00null", "con", "..\\..\\windows"):
            with self.subTest(key=evil):
                scope = server._save_scope(evil)
                self.assertRegex(scope, r"^[0-9a-f]{16}$")
                self.assertNotIn("/", scope)
                self.assertNotIn("\\", scope)
                self.assertNotIn("..", scope)

    def test_a_missing_or_empty_key_still_yields_a_scope(self):
        """An older client sends nothing; it must still get somewhere to save
        rather than crashing or writing to the shared root."""
        for value in (None, "", "   "):
            with self.subTest(value=value):
                self.assertRegex(server._save_scope(value), r"^[0-9a-f]{16}$")

    def test_an_absurdly_long_key_is_bounded(self):
        self.assertRegex(server._save_scope("x" * 100_000), r"^[0-9a-f]{16}$")


class TestSavesAreIsolatedPerScope(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=".")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _system(self, scope):
        game = build_real_game()
        system = SaveLoadSystem(game, save_root=self.root / scope / "saves")
        game.save_load = system
        return game, system

    def test_one_player_cannot_see_another_players_saves(self):
        _, alice = self._system("alice")
        _, bob = self._system("bob")
        alice.save_game("demo")
        self.assertIn("demo", alice.list_saves())
        self.assertIn("No save files", bob.list_saves())

    def test_the_same_name_in_two_scopes_does_not_collide(self):
        alice_game, alice = self._system("alice")
        bob_game, bob = self._system("bob")
        alice_game.player.health = 11
        bob_game.player.health = 3
        alice.save_game("demo")
        bob.save_game("demo")
        alice_game.player.health = 0
        alice.load_game("demo")
        self.assertEqual(alice_game.player.health, 11)

    def test_one_player_cannot_load_another_players_save(self):
        _, alice = self._system("alice")
        _, bob = self._system("bob")
        alice.save_game("secret")
        self.assertIn("not found", bob.load_game("secret"))

    def test_one_player_cannot_delete_another_players_save(self):
        _, alice = self._system("alice")
        _, bob = self._system("bob")
        alice.save_game("demo")
        bob.delete_save("demo")
        self.assertIn("demo", alice.list_saves())


class TestTheServerScopesEachSession(unittest.TestCase):
    def setUp(self):
        for store in (server._sessions, server._input_buffers, server._save_scopes):
            store.clear()
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        for store in (server._sessions, server._save_scopes):
            store.clear()

    def _save_root(self):
        game = next(iter(server._sessions.values()))
        return game.save_load.save_root

    def test_a_client_key_reaches_the_save_root(self):
        self.client.emit("start_game", {"save_key": "browser-one"})
        self.assertIn(server._save_scope("browser-one"), str(self._save_root()))

    def test_two_keys_produce_two_roots(self):
        self.client.emit("start_game", {"save_key": "one"})
        first = self._save_root()
        self.client.emit("start_game", {"save_key": "two"})
        self.assertNotEqual(first, self._save_root())

    def test_reconnecting_with_the_same_key_returns_to_the_same_root(self):
        """This is what keeps `save` then refresh then `load` working."""
        self.client.emit("start_game", {"save_key": "stable"})
        first = self._save_root()
        self.client.emit("start_game", {"save_key": "stable"})
        self.assertEqual(first, self._save_root())

    def test_start_game_still_works_with_no_payload(self):
        """The old client sends nothing at all; it must not break."""
        self.client.emit("start_game")
        self.assertEqual(len(server._sessions), 1)
        self.assertTrue(str(self._save_root()))


if __name__ == "__main__":
    unittest.main()
