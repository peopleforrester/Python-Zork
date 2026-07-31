#!/usr/bin/env python3
"""
ABOUTME: Pins every shipped puzzle's canonical answer against a literal.
ABOUTME: Without this a simulator edit silently rewrites shipped content.
"""

import json
import unittest
from pathlib import Path

from computerquest.mechanics.puzzles import load_registry

_GOLDEN = Path(__file__).parent / "fixtures" / "golden_puzzle_answers.json"


class TestShippedAnswersUnchanged(unittest.TestCase):
    """The canonical answer is recomputed from simulator code on every call and
    stored nowhere, so a simulator change rewrites shipped puzzles silently.

    This was demonstrated, not assumed: making the signature scanner take the
    last match instead of the first flipped `signature_first_match` from
    `boot_sector_virus` to `rootkit_virus`, contradicting the explanation that
    puzzle prints to the player, and the whole suite still passed. These
    assertions close that hole.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = json.loads(_GOLDEN.read_text())
        cls.registry = load_registry()

    def test_every_shipped_puzzle_has_a_pinned_answer(self):
        """A new puzzle must arrive with its answer recorded, not slip in bare."""
        self.assertEqual(sorted(self.registry.by_id), sorted(self.golden))

    def test_canonical_answers_match_the_golden_capture(self):
        for puzzle_id, expected in sorted(self.golden.items()):
            with self.subTest(puzzle=puzzle_id):
                actual = self.registry.canonical_answer(puzzle_id)
                self.assertEqual(
                    actual,
                    expected["canonical_answer"],
                    f"{puzzle_id}: canonical answer changed. If this is intended, "
                    f"update the fixture AND check the puzzle's explanation text "
                    f"still describes the new answer correctly.",
                )

    def test_puzzle_metadata_is_stable(self):
        """Simulator, answer kind, difficulty and subject area all feed grading,
        gating and the knowledge meter; a silent change to any of them moves
        player-visible behaviour."""
        for puzzle_id, expected in sorted(self.golden.items()):
            puzzle = self.registry.by_id[puzzle_id]
            with self.subTest(puzzle=puzzle_id):
                self.assertEqual(puzzle.simulator, expected["simulator"])
                self.assertEqual(puzzle.answer_kind.value, expected["answer_kind"])
                self.assertEqual(puzzle.difficulty, expected["difficulty"])
                self.assertEqual(puzzle.subject_area, expected["subject_area"])

    def test_signature_order_dependence_is_pinned(self):
        """signature_first_match teaches that the scanner walks its DATABASE in
        order, not the file. That lesson rests on YAML preserving mapping order
        into a dict, which is load-bearing and nowhere documented."""
        self.assertEqual(
            self.registry.canonical_answer("signature_first_match"), "boot_sector_virus"
        )
        self.assertEqual(
            self.registry.canonical_answer("signature_near_miss"), "clean"
        )

    def test_the_paired_puzzles_still_diverge(self):
        """Three pairs share a setup and differ only by one policy knob. If a
        pair ever agrees, the knob stopped working and both puzzles lost their
        point."""
        pairs = [
            ("hdd_seek_fcfs", "hdd_seek_sstf"),
            ("pipeline_stall_no_forwarding", "pipeline_forwarding_intro"),
            ("l1_lru_basic", "l1_associativity_2way"),
        ]
        for left, right in pairs:
            with self.subTest(pair=f"{left} vs {right}"):
                self.assertNotEqual(
                    self.registry.canonical_answer(left),
                    self.registry.canonical_answer(right),
                )


if __name__ == "__main__":
    unittest.main()
