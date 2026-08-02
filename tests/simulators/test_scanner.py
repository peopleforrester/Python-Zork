#!/usr/bin/env python3
"""
ABOUTME: Tests for the multi-match and wildcard scanners (PRD 1 Feature B 2-3).
ABOUTME: All expectations hand-derived before implementation.
"""

import unittest

from computerquest.mechanics.simulators.scanner import (
    MultiMatchScanSimulator,
    WildcardScanSimulator,
)
from computerquest.mechanics.simulators.signature import SignatureMatchSimulator

SIGNATURES = {
    "boot_sector_virus": "XJMP:0x7C00",
    "rootkit_virus": "hide_proc(",
}

# The doubly-infected sample from signature_first_match, byte for byte. The
# whole point of the new scanner is that this identical input answers
# differently, which is the policy-knob device every other simulator has.
DOUBLE = "hide_proc(pid); XJMP:0x7C00; done()"

# The recompiled sample from signature_near_miss: one byte off the signature.
NEAR_MISS = "init_sector(); XJMP:0x7C0F; load_mbr()"


class TestMultiMatchScan(unittest.TestCase):
    def test_reports_every_match_in_database_order(self) -> None:
        setup = {"signatures": SIGNATURES, "file_contents": DOUBLE}
        self.assertEqual(
            MultiMatchScanSimulator().run(setup),
            ["boot_sector_virus", "rootkit_virus"],
        )

    def test_database_order_wins_over_position_in_the_file(self) -> None:
        """rootkit_virus appears earlier in the text; the report is still
        ordered by the database, exactly as the single-verdict scanner is."""
        setup = {"signatures": SIGNATURES, "file_contents": DOUBLE}
        self.assertEqual(MultiMatchScanSimulator().run(setup)[0], "boot_sector_virus")

    def test_a_non_matching_entry_gets_a_clean_slot(self) -> None:
        """One slot per database entry, so the answer's length is fixed by the
        database rather than by how many signatures happened to hit. Without
        this the length is part of the answer, and the command layer's
        wrong-shape reply hands the player their token count for free."""
        setup = {"signatures": SIGNATURES, "file_contents": "pad XJMP:0x7C00 pad"}
        self.assertEqual(
            MultiMatchScanSimulator().run(setup), ["boot_sector_virus", "clean"]
        )

    def test_no_match_reports_clean_for_every_entry(self) -> None:
        setup = {"signatures": SIGNATURES, "file_contents": "innocent bytes"}
        self.assertEqual(MultiMatchScanSimulator().run(setup), ["clean", "clean"])

    def test_the_report_is_always_one_slot_per_signature(self) -> None:
        for contents in (DOUBLE, "pad XJMP:0x7C00 pad", "hide_proc(x)", "nothing"):
            with self.subTest(contents=contents):
                report = MultiMatchScanSimulator().run(
                    {"signatures": SIGNATURES, "file_contents": contents}
                )
                self.assertEqual(len(report), len(SIGNATURES))

    def test_it_agrees_with_the_single_verdict_scanner(self) -> None:
        """The contrast has to be additive, or the two puzzles teach noise: the
        first non-clean slot is exactly what the old scanner reports."""
        for contents in (DOUBLE, "pad XJMP:0x7C00 pad", "hide_proc(x)", "nothing"):
            setup = {"signatures": SIGNATURES, "file_contents": contents}
            with self.subTest(contents=contents):
                report = MultiMatchScanSimulator().run(setup)
                first_hit = next((n for n in report if n != "clean"), "clean")
                self.assertEqual(first_hit, SignatureMatchSimulator().run(setup))

    def test_a_signature_matching_twice_is_named_once(self) -> None:
        setup = {"signatures": SIGNATURES, "file_contents": DOUBLE + " " + DOUBLE}
        self.assertEqual(
            MultiMatchScanSimulator().run(setup),
            ["boot_sector_virus", "rootkit_virus"],
        )


class TestWildcardScan(unittest.TestCase):
    WILDCARD = {
        "boot_sector_virus": "XJMP:0x7C0?",
        "rootkit_virus": "hide_*(",
    }

    def test_exact_mode_reproduces_the_original_scanner(self) -> None:
        """The knob's other position must be the behaviour already shipped, or
        the contrast is between a new thing and a different new thing."""
        for contents in (DOUBLE, NEAR_MISS, "innocent bytes"):
            setup = {"signatures": SIGNATURES, "file_contents": contents, "mode": "exact"}
            with self.subTest(contents=contents):
                self.assertEqual(
                    WildcardScanSimulator().run(setup),
                    SignatureMatchSimulator().run(setup),
                )

    def test_wildcard_catches_the_one_byte_mutation(self) -> None:
        """signature_near_miss reports clean; the same file under a wildcard
        pattern is a match. That is the IOU its explanation leaves open."""
        setup = {
            "signatures": self.WILDCARD,
            "file_contents": NEAR_MISS,
            "mode": "wildcard",
        }
        self.assertEqual(WildcardScanSimulator().run(setup), "boot_sector_virus")

    def test_the_same_file_is_clean_under_exact_matching(self) -> None:
        setup = {"signatures": self.WILDCARD, "file_contents": NEAR_MISS, "mode": "exact"}
        self.assertEqual(WildcardScanSimulator().run(setup), "clean")

    def test_star_spans_several_characters(self) -> None:
        setup = {
            "signatures": self.WILDCARD,
            "file_contents": "hide_process(pid)",
            "mode": "wildcard",
        }
        self.assertEqual(WildcardScanSimulator().run(setup), "rootkit_virus")

    def test_question_mark_spans_exactly_one_character(self) -> None:
        setup = {
            "signatures": {"boot_sector_virus": "XJMP:0x7C0?"},
            "file_contents": "XJMP:0x7C0",   # nothing left for ? to consume
            "mode": "wildcard",
        }
        self.assertEqual(WildcardScanSimulator().run(setup), "clean")

    def test_regex_metacharacters_in_a_signature_are_literal(self) -> None:
        """Signatures are byte patterns, not regexes. A '.' must not match 'x',
        or an author writing a real-looking signature gets silent false hits."""
        setup = {
            "signatures": {"boot_sector_virus": "a.c"},
            "file_contents": "abc",
            "mode": "wildcard",
        }
        self.assertEqual(WildcardScanSimulator().run(setup), "clean")

    def test_first_match_in_database_order_still_wins(self) -> None:
        setup = {
            "signatures": self.WILDCARD,
            "file_contents": DOUBLE,
            "mode": "wildcard",
        }
        self.assertEqual(WildcardScanSimulator().run(setup), "boot_sector_virus")

    def test_an_unknown_mode_is_an_author_error(self) -> None:
        setup = {"signatures": SIGNATURES, "file_contents": DOUBLE, "mode": "fuzzy"}
        with self.assertRaises(ValueError):
            WildcardScanSimulator().run(setup)

    def test_mode_defaults_to_exact(self) -> None:
        setup = {"signatures": SIGNATURES, "file_contents": DOUBLE}
        self.assertEqual(WildcardScanSimulator().run(setup), "boot_sector_virus")


class TestScannerInputBounds(unittest.TestCase):
    """The registry validates a puzzle by running it, so an author-supplied
    quantity is executed at load time. Wildcards make that a regex search."""

    def test_an_oversized_file_is_rejected(self) -> None:
        setup = {
            "signatures": SIGNATURES,
            "file_contents": "x" * (1 << 22),
            "mode": "wildcard",
        }
        with self.assertRaises(ValueError):
            WildcardScanSimulator().run(setup)

    def test_too_many_signatures_are_rejected(self) -> None:
        setup = {
            "signatures": {f"v{i}": f"sig{i}" for i in range(5000)},
            "file_contents": "harmless",
        }
        with self.assertRaises(ValueError):
            MultiMatchScanSimulator().run(setup)


if __name__ == "__main__":
    unittest.main()
