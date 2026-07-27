#!/usr/bin/env python3
"""
ABOUTME: Pins player.knowledge to exactly one writer, the puzzle recompute.
ABOUTME: A reward that bumped knowledge directly was silently wiped on solve.
"""

import unittest

from tests._helpers import build_real_game


class TestKnowledgeHasOneWriter(unittest.TestCase):
    """Contract (docs/architecture-microquiz.md, Knowledge meter): knowledge is
    a function of solved puzzles. Nothing else may grant it, because a second
    writer's grant is silently discarded by the next recompute."""

    def setUp(self) -> None:
        self.game = build_real_game()

    def test_reward_does_not_grant_knowledge(self):
        """An achievement reward must not move the knowledge meter.

        Before the fix this appeared to work, then vanished on the next solve,
        which is worse than not granting it at all.
        """
        before = self.game.player.knowledge["cpu"]
        self.game.progress.apply_reward({"knowledge": "cpu", "amount": 2})
        self.assertEqual(self.game.player.knowledge["cpu"], before)

    def test_reward_still_grants_items(self):
        """Item rewards are orthogonal to the knowledge model and still work."""
        self.game.progress.apply_reward({"item": "trophy", "description": "A shiny trophy"})
        self.assertIn("trophy", self.game.player.items)
        self.assertEqual(self.game.player.items["trophy"], "A shiny trophy")

    def test_knowledge_survives_a_recompute_because_it_is_derived(self):
        """Whatever grants knowledge must be visible to the recompute, or it
        is not durable. Solving a puzzle is; a direct write is not."""
        registry = self.game.puzzle_registry
        puzzle = registry.by_id["l1_lru_basic"]
        self.game.player.solved_puzzles.add(puzzle.id)
        self.game._recompute_knowledge()
        earned = self.game.player.knowledge[puzzle.subject_area]
        self.assertGreater(earned, 0)

        # A direct write is not part of the model, so it does not survive.
        self.game.player.knowledge[puzzle.subject_area] = 5
        self.game._recompute_knowledge()
        self.assertEqual(self.game.player.knowledge[puzzle.subject_area], earned)


if __name__ == "__main__":
    unittest.main()
