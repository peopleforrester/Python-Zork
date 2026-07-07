#!/usr/bin/env python3
"""
ABOUTME: Tests for SaveLoadSystem — serialize/load roundtrip + edge cases.
ABOUTME: Uses tmp_path so saves never land in the user's real home dir.
"""

import json
import pathlib
import unittest

from computerquest.mechanics.save_load import SAVE_SCHEMA_VERSION, SaveLoadSystem
from tests._helpers import build_real_game


class SaveLoadTestBase(unittest.TestCase):
    """Build a real Game + a SaveLoadSystem rooted in a fresh tmp dir."""

    def setUp(self) -> None:
        self.game = build_real_game()
        # Per-test temp dir so saves never escape the test scope.
        self._tmp_root = pathlib.Path(self.id().replace(".", "_") + "_saves")
        self._tmp_root.mkdir(exist_ok=True)
        self.save_root = self._tmp_root
        self.save_load = SaveLoadSystem(self.game, save_root=self.save_root)
        # Replace the game's bound save_load so commands route here too.
        self.game.save_load = self.save_load

    def tearDown(self) -> None:
        for p in self.save_root.glob("*.json"):
            p.unlink()
        try:
            self.save_root.rmdir()
        except OSError:
            pass


class TestSaveGame(SaveLoadTestBase):
    def test_save_with_explicit_name_writes_json_file(self) -> None:
        result = self.save_load.save_game("explicit_name")
        path = self.save_root / "explicit_name.json"
        self.assertTrue(path.exists())
        self.assertIn("explicit_name", result)

    def test_save_appends_json_extension(self) -> None:
        self.save_load.save_game("no_ext")
        self.assertTrue((self.save_root / "no_ext.json").exists())

    def test_save_with_no_name_generates_timestamped_default(self) -> None:
        result = self.save_load.save_game()
        saved = list(self.save_root.glob("kodekloud_quest_save_*.json"))
        self.assertEqual(len(saved), 1)
        self.assertIn(saved[0].stem, result)

    def test_save_captures_player_and_world_state(self) -> None:
        self.game.player.health = 13
        self.game.player.knowledge["cpu"] = 4
        self.game.player.found_viruses.append("boot_sector_virus")
        self.game.turns = 42

        self.save_load.save_game("snapshot")
        data = json.loads((self.save_root / "snapshot.json").read_text())

        self.assertEqual(data["version"], SAVE_SCHEMA_VERSION)
        self.assertEqual(data["turns"], 42)
        self.assertEqual(data["player"]["health"], 13)
        self.assertEqual(data["player"]["knowledge"]["cpu"], 4)
        self.assertIn("boot_sector_virus", data["player"]["found_viruses"])


class TestLoadGame(SaveLoadTestBase):
    def test_roundtrip_restores_state(self) -> None:
        # Mutate state, save, mutate again, load — restored state should match
        # the saved snapshot, not the post-save mutations.
        self.game.player.health = 7
        # Knowledge is derived from solved puzzles since the microquiz
        # cutover; seed a solve rather than poking the meter directly.
        self.game.player.solved_puzzles.add("virus_signature_match")
        self.game.player.found_viruses.append("rootkit_virus")
        self.game.turns = 15
        self.save_load.save_game("checkpoint")

        # Post-save mutations
        self.game.player.health = 20
        self.game.player.solved_puzzles.clear()
        self.game.player.found_viruses.clear()
        self.game.turns = 99

        result = self.save_load.load_game("checkpoint")
        self.assertIn("Game loaded", result)
        self.assertEqual(self.game.turns, 15)
        self.assertEqual(self.game.player.health, 7)
        # virus_signature_match is difficulty 1 -> security knowledge 1.
        self.assertEqual(self.game.player.knowledge["security"], 1)
        self.assertIn("rootkit_virus", self.game.player.found_viruses)

    def test_load_missing_file_returns_clear_message(self) -> None:
        result = self.save_load.load_game("does_not_exist")
        self.assertIn("not found", result)

    def test_load_rejects_incompatible_schema_version(self) -> None:
        bad = self.save_root / "future.json"
        bad.write_text(json.dumps({"version": "9.0", "turns": 0}))
        result = self.save_load.load_game("future")
        self.assertIn("incompatible", result)

    def test_load_corrupt_json_returns_error_message(self) -> None:
        corrupt = self.save_root / "corrupt.json"
        corrupt.write_text("{not valid json")
        result = self.save_load.load_game("corrupt")
        self.assertIn("Error loading", result)

    def test_load_missing_field_returns_clear_message(self) -> None:
        partial = self.save_root / "partial.json"
        partial.write_text(json.dumps({"version": SAVE_SCHEMA_VERSION}))
        result = self.save_load.load_game("partial")
        self.assertIn("missing required field", result)


class TestSchemaMigration(SaveLoadTestBase):
    """Microquiz step 3: schema 1.1 adds puzzle progress; 1.0 saves still load."""

    def test_puzzle_progress_roundtrips(self) -> None:
        self.game.player.solved_puzzles.add("l1_lru_basic")
        self.game.player.attempted_puzzles.update({"l1_lru_basic", "pipeline_forwarding_intro"})
        self.save_load.save_game("with_puzzles")

        self.game.player.solved_puzzles.clear()
        self.game.player.attempted_puzzles.clear()

        result = self.save_load.load_game("with_puzzles")
        self.assertIn("Game loaded", result)
        self.assertEqual(self.game.player.solved_puzzles, {"l1_lru_basic"})
        self.assertEqual(
            self.game.player.attempted_puzzles,
            {"l1_lru_basic", "pipeline_forwarding_intro"},
        )

    def test_saves_write_schema_1_1(self) -> None:
        self.save_load.save_game("versioned")
        data = json.loads((self.save_root / "versioned.json").read_text())
        self.assertEqual(data["version"], SAVE_SCHEMA_VERSION)
        self.assertEqual(data["version"], "1.1")

    def test_schema_1_0_save_still_loads_with_empty_puzzle_sets(self) -> None:
        """A pre-microquiz save has no puzzle fields; loading must succeed
        and initialize them empty rather than rejecting or crashing."""
        self.game.player.solved_puzzles.add("l1_lru_basic")
        self.save_load.save_game("legacy")
        path = self.save_root / "legacy.json"
        data = json.loads(path.read_text())
        data["version"] = "1.0"
        del data["player"]["solved_puzzles"]
        del data["player"]["attempted_puzzles"]
        path.write_text(json.dumps(data))

        result = self.save_load.load_game("legacy")
        self.assertIn("Game loaded", result)
        self.assertEqual(self.game.player.solved_puzzles, set())
        self.assertEqual(self.game.player.attempted_puzzles, set())


class TestListSaves(SaveLoadTestBase):
    def test_empty_directory_reports_no_files(self) -> None:
        self.assertIn("No save files", self.save_load.list_saves())

    def test_list_reflects_existing_saves(self) -> None:
        self.save_load.save_game("alpha")
        self.save_load.save_game("beta")
        listing = self.save_load.list_saves()
        self.assertIn("alpha", listing)
        self.assertIn("beta", listing)


class TestDeleteSave(SaveLoadTestBase):
    def test_delete_removes_file(self) -> None:
        self.save_load.save_game("gone")
        self.assertTrue((self.save_root / "gone.json").exists())

        result = self.save_load.delete_save("gone")
        self.assertIn("deleted", result.lower())
        self.assertFalse((self.save_root / "gone.json").exists())

    def test_delete_missing_file_returns_clear_message(self) -> None:
        result = self.save_load.delete_save("never_existed")
        self.assertIn("not found", result)


if __name__ == "__main__":
    unittest.main()
