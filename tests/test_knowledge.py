#!/usr/bin/env python3
"""
ABOUTME: Tests for the knowledge-meter cutover (microquiz step 6).
ABOUTME: Knowledge derives from solved puzzles only; visits and scans grant nothing.
"""

import unittest

from tests._helpers import build_real_game


class TestKnowledgeFromPuzzles(unittest.TestCase):
    def setUp(self) -> None:
        self.game = build_real_game()

    def solve_l1_lru(self) -> None:
        self.game.player.location = self.game.game_map.rooms["core1_l1"]
        self.game.feed("solve l1_lru_basic")
        self.game.feed("answer M M M M H M H")

    def test_difficulty_one_solve_grants_one_point(self) -> None:
        self.solve_l1_lru()
        self.assertEqual(self.game.player.knowledge["memory"], 1)

    def test_weights_accumulate_by_difficulty(self) -> None:
        """Difficulty 1 contributes 1.0; difficulty 2 contributes 1.5."""
        self.solve_l1_lru()
        self.game.feed("solve l1_associativity_2way")
        self.game.feed("answer M M M M H M H H")
        self.assertEqual(self.game.player.knowledge["memory"], 2.5)

    def test_cap_at_five(self) -> None:
        registry = self.game.puzzle_registry
        for puzzle in registry.by_id.values():
            if puzzle.subject_area == "memory":
                self.game.player.solved_puzzles.add(puzzle.id)
        self.game._recompute_knowledge()
        self.assertEqual(self.game.player.knowledge["memory"], 5)

    def test_wrong_answer_grants_nothing(self) -> None:
        self.game.player.location = self.game.game_map.rooms["core1_l1"]
        self.game.feed("solve l1_lru_basic")
        self.game.feed("answer H H H H H H H")
        self.assertEqual(self.game.player.knowledge["memory"], 0)


class TestNonPuzzleActionsGrantNothing(unittest.TestCase):
    def setUp(self) -> None:
        self.game = build_real_game()

    def test_visiting_and_scanning_grant_nothing(self) -> None:
        self.game.feed("n")      # into core1 (a cpu room)
        self.game.feed("skip")
        self.game.feed("look")
        self.game.feed("sc")     # clean-room scan used to bump component knowledge
        self.assertTrue(all(v == 0 for v in self.game.player.knowledge.values()))

    def test_quarantine_no_longer_bumps_security(self) -> None:
        self.game.player.location = self.game.game_map.rooms["ram_dimm1"]
        self.game.feed("sc")
        self.game.feed("quarantine memory_resident_virus")
        self.assertIn("memory_resident_virus", self.game.player.quarantined_viruses)
        self.assertEqual(self.game.player.knowledge["security"], 0)


class TestLoadRecomputes(unittest.TestCase):
    def test_stored_knowledge_is_ignored_and_rederived(self) -> None:
        import json

        game = build_real_game()
        game.save_load.save_root = None  # replaced below
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            game.save_load.save_root = Path(tmp)
            game.player.solved_puzzles.add("l1_lru_basic")
            game.save_load.save_game("k")

            path = Path(tmp) / "k.json"
            data = json.loads(path.read_text())
            data["player"]["knowledge"]["memory"] = 4  # stale pre-cutover value
            path.write_text(json.dumps(data))

            game.save_load.load_game("k")
            self.assertEqual(game.player.knowledge["memory"], 1)


if __name__ == "__main__":
    unittest.main()
