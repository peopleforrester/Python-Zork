#!/usr/bin/env python3
"""
ABOUTME: Integration tests for the solve/answer/hint/skip command surface.
ABOUTME: Exercises the feed() path the web server depends on (contract layer 3).
"""

import unittest

from tests._helpers import build_real_game


class MicroquizCommandBase(unittest.TestCase):
    def setUp(self) -> None:
        self.game = build_real_game()

    def go_to_core1_l1(self) -> None:
        """cpu_package -> core1 (n) -> core1_l1 (s)."""
        self.game.feed("n")
        self.game.feed("s")


class TestSolve(MicroquizCommandBase):
    def test_solve_in_room_without_puzzles_reports_none(self) -> None:
        # cpu_package has no bound puzzles.
        result = self.game.feed("solve")
        self.assertIn("no puzzle", result.lower())

    def test_solve_activates_the_rooms_primary_puzzle(self) -> None:
        self.go_to_core1_l1()
        result = self.game.feed("solve")
        self.assertIsNotNone(self.game.current_puzzle)
        self.assertEqual(self.game.current_puzzle.id, "l1_lru_basic")
        self.assertIn("seven tokens of H or M", result)  # grammar shown

    def test_solve_by_id_bypasses_difficulty_gating(self) -> None:
        self.go_to_core1_l1()
        result = self.game.feed("solve l1_associativity_2way")
        self.assertEqual(self.game.current_puzzle.id, "l1_associativity_2way")
        self.assertIn("eight tokens", result)

    def test_solve_listing_soft_gates_higher_difficulty(self) -> None:
        """Difficulty-2 puzzles stay out of the listing until a
        difficulty-1 puzzle in the same area is solved (decision 2)."""
        self.go_to_core1_l1()
        self.game.feed("skip")  # dismiss the auto-prompted primary
        self.game.current_puzzle = None
        listing = self.game.list_room_puzzles()
        self.assertIn("l1_lru_basic", listing)
        self.assertNotIn("l1_associativity_2way", listing)

        self.game.player.solved_puzzles.add("l1_lru_basic")
        listing = self.game.list_room_puzzles()
        self.assertIn("l1_associativity_2way", listing)

    def test_solve_unknown_id_reports_clearly(self) -> None:
        self.go_to_core1_l1()
        result = self.game.feed("solve made_up_puzzle")
        self.assertIn("no puzzle", result.lower())


class TestAnswer(MicroquizCommandBase):
    def setUp(self) -> None:
        super().setUp()
        self.go_to_core1_l1()
        self.game.feed("solve")

    def test_answer_without_active_puzzle(self) -> None:
        self.game.feed("skip")
        result = self.game.feed("answer H M H")
        self.assertIn("no active puzzle", result.lower())

    def test_correct_answer_solves_and_explains(self) -> None:
        result = self.game.feed("answer M M M M H M H")
        self.assertIn("l1_lru_basic", self.game.player.solved_puzzles)
        self.assertIn("l1_lru_basic", self.game.player.attempted_puzzles)
        self.assertIsNone(self.game.current_puzzle)
        self.assertIn("Direct mapping is brutal", result)  # explanation shown

    def test_wrong_answer_records_attempt_with_position_feedback(self) -> None:
        result = self.game.feed("answer M M M M H H H")
        self.assertNotIn("l1_lru_basic", self.game.player.solved_puzzles)
        self.assertIn("l1_lru_basic", self.game.player.attempted_puzzles)
        self.assertIsNone(self.game.current_puzzle)  # ends on commit
        self.assertIn("6 of 7", result)

    def test_wrong_shape_is_not_graded(self) -> None:
        result = self.game.feed("answer H M")  # wrong length
        self.assertIn("I need an answer like", result)
        self.assertNotIn("l1_lru_basic", self.game.player.attempted_puzzles)
        self.assertIsNotNone(self.game.current_puzzle)  # still active

    def test_answer_dirties_save_state_but_solve_does_not(self) -> None:
        # Movement in setUp already dirtied the flag; reset to isolate.
        self.game.changes_since_save = False
        self.game.feed("solve")  # re-presenting is read-only
        self.assertFalse(self.game.changes_since_save)
        self.game.feed("answer M M M M H M H")
        self.assertTrue(self.game.changes_since_save)


class TestHintAndSkip(MicroquizCommandBase):
    def setUp(self) -> None:
        super().setUp()
        self.go_to_core1_l1()
        self.game.feed("solve")

    def test_first_hint_is_free(self) -> None:
        result = self.game.feed("hint")
        self.assertIn("cache line", result.lower())
        self.assertNotIn("l1_lru_basic", self.game.player.attempted_puzzles)

    def test_second_hint_marks_attempted(self) -> None:
        self.game.feed("hint")
        result = self.game.feed("hint")
        self.assertIn("same set", result.lower())
        self.assertIn("l1_lru_basic", self.game.player.attempted_puzzles)

    def test_hint_without_active_puzzle(self) -> None:
        self.game.feed("skip")
        result = self.game.feed("hint")
        self.assertIn("no active puzzle", result.lower())

    def test_skip_clears_without_recording(self) -> None:
        result = self.game.feed("skip")
        self.assertIsNone(self.game.current_puzzle)
        self.assertNotIn("l1_lru_basic", self.game.player.attempted_puzzles)
        self.assertIn("aside", result.lower())


class TestAutoPromptAndLook(MicroquizCommandBase):
    def test_first_entry_auto_presents_the_primary_puzzle(self) -> None:
        result = self.game.feed("n")  # into core1, which binds the pipeline intro
        self.assertIn("Pipeline", result)
        self.assertIn("skip", result.lower())
        self.assertEqual(self.game.current_puzzle.id, "pipeline_forwarding_intro")

    def test_second_entry_does_not_re_prompt(self) -> None:
        self.game.feed("n")
        self.game.feed("skip")
        self.game.feed("s")   # core1 -> core1_l1 (auto-prompts its own primary)
        self.game.feed("skip")
        self.game.feed("n")   # core1_l1 -> core1 again: already prompted
        result = self.game.feed("look")
        # Re-entry shows the look hint, not a full re-presentation.
        self.assertIsNone(self.game.current_puzzle)
        self.assertIn("[ puzzle available:", result)

    def test_look_hints_at_unsolved_puzzles(self) -> None:
        self.game.feed("n")
        self.game.feed("skip")
        result = self.game.feed("look")
        self.assertIn("[ puzzle available: Pipeline", result)

    def test_look_hint_disappears_once_solved(self) -> None:
        self.game.feed("n")
        self.game.feed("skip")
        self.game.player.solved_puzzles.add("pipeline_forwarding_intro")
        result = self.game.feed("look")
        self.assertNotIn("[ puzzle available:", result)


if __name__ == "__main__":
    unittest.main()
