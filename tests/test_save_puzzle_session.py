#!/usr/bin/env python3
"""
ABOUTME: In-flight puzzle state survives save/load (schema 1.2).
ABOUTME: Restore is tolerant: content can change between saving and loading.
"""

import json
import tempfile
import unittest
from pathlib import Path

from computerquest.mechanics.save_load import SAVE_SCHEMA_VERSION
from tests._helpers import build_real_game


class _SaveDir(unittest.TestCase):
    """Each test saves into its own directory so runs cannot collide."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.game = build_real_game()
        self.game.save_load.save_root = Path(self._tmp.name)

    def _roundtrip(self, name="t"):
        self.game.save_load.save_game(name)
        fresh = build_real_game()
        fresh.save_load.save_root = Path(self._tmp.name)
        fresh.save_load.load_game(name)
        return fresh

    def _saved_json(self, name="t"):
        return json.loads((Path(self._tmp.name) / f"{name}.json").read_text())


class TestSchemaVersion(_SaveDir):
    def test_version_is_current(self):
        """A literal, so a bump is a conscious edit rather than a side effect."""
        self.assertEqual(SAVE_SCHEMA_VERSION, "1.3")

    def test_saves_declare_the_new_version(self):
        self.game.save_load.save_game("t")
        self.assertEqual(self._saved_json()["version"], "1.3")

    def test_a_1_2_save_still_loads(self):
        """1.2 predates hint_mode; it must restore the standard bargain."""
        self.game.save_load.save_game("t")
        path = Path(self._tmp.name) / "t.json"
        data = json.loads(path.read_text())
        data["version"] = "1.2"
        data["puzzle_session"].pop("hint_mode", None)
        path.write_text(json.dumps(data))

        fresh = build_real_game()
        fresh.save_load.save_root = Path(self._tmp.name)
        self.assertNotIn("incompatible", fresh.save_load.load_game("t").lower())
        self.assertEqual(fresh.puzzles.hint_mode.value, "standard")

    def test_a_1_1_save_still_loads(self):
        """Additive change, so the previous version must keep working."""
        self.game.save_load.save_game("t")
        path = Path(self._tmp.name) / "t.json"
        data = json.loads(path.read_text())
        data["version"] = "1.1"
        data.pop("puzzle_session", None)
        path.write_text(json.dumps(data))

        fresh = build_real_game()
        fresh.save_load.save_root = Path(self._tmp.name)
        result = fresh.save_load.load_game("t")
        self.assertNotIn("incompatible", result.lower())
        self.assertIsNone(fresh.current_puzzle)
        self.assertEqual(fresh.puzzle_hints_used, 0)


class TestActivePuzzleRoundtrips(_SaveDir):
    def test_active_puzzle_and_hint_count_survive(self):
        self.game.feed("n")            # Core 1
        self.game.feed("s")            # Core 1 L1 Cache
        self.game.feed("solve l1_lru_basic")
        self.game.feed("hint")
        self.assertIsNotNone(self.game.current_puzzle)

        fresh = self._roundtrip()
        self.assertIsNotNone(fresh.current_puzzle)
        self.assertEqual(fresh.current_puzzle.id, "l1_lru_basic")
        self.assertEqual(fresh.puzzle_hints_used, 1)

    def test_answering_after_a_load_works(self):
        """A restored puzzle must be genuinely active, not just recorded."""
        self.game.feed("n")
        self.game.feed("s")
        self.game.feed("solve l1_lru_basic")
        fresh = self._roundtrip()
        out = fresh.feed("answer M M M M H M H")
        self.assertIn("Correct!", out)
        self.assertIn("l1_lru_basic", fresh.player.solved_puzzles)

    def test_no_active_puzzle_saves_as_null(self):
        self.game.save_load.save_game("t")
        self.assertIsNone(self._saved_json()["puzzle_session"]["current"])
        self.assertIsNone(self._roundtrip().current_puzzle)

    def test_the_puzzle_body_is_not_serialized(self):
        """Only the id belongs in the file; the body must come from disk, or a
        stale save could resurrect deleted content."""
        self.game.feed("n")
        self.game.feed("s")
        self.game.feed("solve l1_lru_basic")
        self.game.save_load.save_game("t")
        blob = self._saved_json()["puzzle_session"]
        self.assertEqual(blob["current"], "l1_lru_basic")
        # Compare against the real body, not the word "prompt", which is a
        # substring of the prompted_rooms key.
        puzzle = self.game.puzzle_registry.by_id["l1_lru_basic"]
        serialized = json.dumps(blob)
        self.assertNotIn(puzzle.prompt[:30], serialized)
        self.assertNotIn(puzzle.explanation[:30], serialized)
        self.assertEqual(
            set(blob), {"current", "hints_used", "prompted_rooms", "hint_mode"}
        )


class TestPromptedRoomsRoundtrips(_SaveDir):
    """prompted_rooms is what actually stops a room re-offering its puzzle.
    Restoring the active puzzle alone does not: auto-prompt only bails while a
    puzzle is active, so re-prompting resumes the moment one is answered."""

    def test_prompted_rooms_survive(self):
        self.game.feed("n")
        self.game.feed("s")
        self.assertTrue(self.game.prompted_rooms)
        before = set(self.game.prompted_rooms)
        self.assertEqual(set(self._roundtrip().prompted_rooms), before)

    def test_a_skipped_room_does_not_re_prompt_after_loading(self):
        """Skip records no attempt, so before this change the room auto-prompted
        again on every load. That is the exact complaint being fixed."""
        # Entering core1 auto-prompts its puzzle. (core1_l1 does not prompt on
        # arrival because auto-prompt bails while a puzzle is already active.)
        self.game.feed("n")
        self.game.feed("skip")         # skip records no attempt
        self.assertIn("core1", self.game.prompted_rooms)

        fresh = self._roundtrip()
        # Walk out and back in; the room must stay quiet.
        fresh.feed("s")
        re_entry = fresh.feed("n")
        self.assertNotIn("PUZZLE:", re_entry)


class TestTolerantRestore(_SaveDir):
    """Content changes between saving and loading; a save must degrade, not die.
    This follows the loader's existing precedent for unknown component ids."""

    def test_unknown_puzzle_id_is_dropped_not_fatal(self):
        self.game.save_load.save_game("t")
        path = Path(self._tmp.name) / "t.json"
        data = json.loads(path.read_text())
        data["puzzle_session"]["current"] = "puzzle_deleted_since_this_save"
        data["puzzle_session"]["hints_used"] = 3
        path.write_text(json.dumps(data))

        fresh = build_real_game()
        fresh.save_load.save_root = Path(self._tmp.name)
        result = fresh.save_load.load_game("t")
        self.assertIn("loaded", result.lower())
        self.assertIsNone(fresh.current_puzzle)
        self.assertEqual(fresh.puzzle_hints_used, 0)

    def test_hints_used_is_clamped_to_the_puzzles_hint_count(self):
        """A shortened hint list must not leave a nonsense counter behind."""
        self.game.feed("n")
        self.game.feed("s")
        self.game.feed("solve l1_lru_basic")
        self.game.save_load.save_game("t")
        path = Path(self._tmp.name) / "t.json"
        data = json.loads(path.read_text())
        data["puzzle_session"]["hints_used"] = 99
        path.write_text(json.dumps(data))

        fresh = build_real_game()
        fresh.save_load.save_root = Path(self._tmp.name)
        fresh.save_load.load_game("t")
        available = len(fresh.puzzle_registry.by_id["l1_lru_basic"].hints)
        self.assertLessEqual(fresh.puzzle_hints_used, available)

    def test_unknown_prompted_room_is_inert(self):
        self.game.save_load.save_game("t")
        path = Path(self._tmp.name) / "t.json"
        data = json.loads(path.read_text())
        data["puzzle_session"]["prompted_rooms"] = ["a_room_that_no_longer_exists"]
        path.write_text(json.dumps(data))

        fresh = build_real_game()
        fresh.save_load.save_root = Path(self._tmp.name)
        self.assertIn("loaded", fresh.save_load.load_game("t").lower())


class TestKnowledgeStillDerived(_SaveDir):
    def test_restoring_a_session_does_not_grant_knowledge(self):
        """PuzzleSession stays the single writer; an in-flight puzzle is not a
        solved one."""
        self.game.feed("n")
        self.game.feed("s")
        self.game.feed("solve l1_lru_basic")
        fresh = self._roundtrip()
        self.assertEqual(fresh.player.knowledge["memory"], 0)


if __name__ == "__main__":
    unittest.main()
