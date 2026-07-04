#!/usr/bin/env python3
"""
ABOUTME: Tests for the simulator shared types — AnswerKind, Verdict, verify().
ABOUTME: Contract: docs/architecture-microquiz.md (sha256:cde83dbaa90b).
"""

import unittest

from computerquest.mechanics.simulators.base import (
    AnswerKind,
    Verdict,
    verify_sequence,
)


class TestVerifySequence(unittest.TestCase):
    def test_full_match_is_correct(self) -> None:
        verdict = verify_sequence(["H", "M", "H"], ["H", "M", "H"])
        self.assertIsInstance(verdict, Verdict)
        self.assertTrue(verdict.correct)
        self.assertTrue(all(p.matched for p in verdict.positions))

    def test_single_mismatch_flags_position_and_fails(self) -> None:
        verdict = verify_sequence(["H", "H", "H"], ["H", "M", "H"])
        self.assertFalse(verdict.correct)
        matched = [p.matched for p in verdict.positions]
        self.assertEqual(matched, [True, False, True])
        # The mismatching position carries both values for the diff render.
        bad = verdict.positions[1]
        self.assertEqual(bad.given, "H")
        self.assertEqual(bad.expected, "M")

    def test_case_and_whitespace_insensitive(self) -> None:
        verdict = verify_sequence([" h", "m "], ["H", "M"])
        self.assertTrue(verdict.correct)

    def test_length_mismatch_is_incorrect_not_an_exception(self) -> None:
        verdict = verify_sequence(["H"], ["H", "M"])
        self.assertFalse(verdict.correct)
        self.assertIn("expected 2", verdict.summary)

    def test_summary_counts_matches(self) -> None:
        verdict = verify_sequence(["H", "H", "M"], ["H", "M", "M"])
        self.assertIn("2 of 3", verdict.summary)


class TestAnswerKind(unittest.TestCase):
    def test_expected_members(self) -> None:
        for member in ("CHOICE", "SEQUENCE", "NUMBER", "BOOL", "MAPPING"):
            self.assertTrue(hasattr(AnswerKind, member))

    def test_values_are_strings(self) -> None:
        self.assertEqual(AnswerKind.SEQUENCE.value, "sequence")


if __name__ == "__main__":
    unittest.main()
