#!/usr/bin/env python3
"""
ABOUTME: Tests for the educational cache simulator (hit/miss prediction).
ABOUTME: Expectations hand-derived from the P&H direct-mapped/set-associative model.
"""

import unittest

from computerquest.mechanics.simulators.cache import CacheSimulator

# The l1_lru_basic example from docs/architecture-microquiz.md: 4-line
# direct-mapped cache, 64-byte lines, LRU. Line numbers for the accesses are
# 4,5,6,7,4,8,5; with 4 sets the indexes are 0,1,2,3,0,0,1. Access 6 (0x200,
# line 8) maps to set 0 and evicts line 4 (0x100).
DOC_EXAMPLE = {
    "policy": "LRU",
    "size_lines": 4,
    "line_size_bytes": 64,
    "associativity": 1,
    "accesses": [0x0100, 0x0140, 0x0180, 0x01C0, 0x0100, 0x0200, 0x0140],
}


class TestDirectMapped(unittest.TestCase):
    def test_doc_example_hit_miss_sequence(self) -> None:
        result = CacheSimulator().run(DOC_EXAMPLE)
        self.assertEqual(result, ["M", "M", "M", "M", "H", "M", "H"])

    def test_conflict_eviction_re_miss(self) -> None:
        """After 0x200 evicts 0x100 from set 0 (direct-mapped), a further
        0x100 access misses again."""
        setup = dict(DOC_EXAMPLE)
        setup["accesses"] = DOC_EXAMPLE["accesses"] + [0x0100]
        result = CacheSimulator().run(setup)
        self.assertEqual(result[-1], "M")

    def test_same_line_offsets_hit(self) -> None:
        """Two addresses inside one 64-byte line are one cache line: the
        second access hits (spatial locality)."""
        setup = {
            "policy": "LRU",
            "size_lines": 4,
            "line_size_bytes": 64,
            "associativity": 1,
            "accesses": [0x0100, 0x0104, 0x013F],
        }
        self.assertEqual(CacheSimulator().run(setup), ["M", "H", "H"])


class TestSetAssociative(unittest.TestCase):
    def test_two_way_rescues_the_conflict(self) -> None:
        """Same doc accesses at 2-way associativity: 0x200 evicts the LRU
        line of set 0 (0x180, untouched since load), so a further 0x100
        access hits — the 'associativity rescue' the doc's follow-up
        puzzle teaches."""
        setup = dict(DOC_EXAMPLE)
        setup["associativity"] = 2
        setup["accesses"] = DOC_EXAMPLE["accesses"] + [0x0100]
        result = CacheSimulator().run(setup)
        # First seven accesses produce the same H/M pattern as direct-mapped
        # (the rescue shows on the eighth access, not before).
        self.assertEqual(result[:7], ["M", "M", "M", "M", "H", "M", "H"])
        self.assertEqual(result[7], "H")


class TestReplacementPolicies(unittest.TestCase):
    """A-B-A-C-A on a 2-line fully-associative cache discriminates LRU from
    FIFO: after A B A, LRU order is (B, A) so C evicts B and the final A
    hits; FIFO order is (A, B) so C evicts A and the final A misses."""

    ACCESSES = [0x000, 0x040, 0x000, 0x080, 0x000]

    def _setup(self, policy: str) -> dict:
        return {
            "policy": policy,
            "size_lines": 2,
            "line_size_bytes": 64,
            "associativity": 2,
            "accesses": self.ACCESSES,
        }

    def test_lru(self) -> None:
        self.assertEqual(
            CacheSimulator().run(self._setup("LRU")), ["M", "M", "H", "M", "H"]
        )

    def test_fifo(self) -> None:
        self.assertEqual(
            CacheSimulator().run(self._setup("FIFO")), ["M", "M", "H", "M", "M"]
        )


class TestValidation(unittest.TestCase):
    def test_empty_accesses_returns_empty(self) -> None:
        setup = dict(DOC_EXAMPLE)
        setup["accesses"] = []
        self.assertEqual(CacheSimulator().run(setup), [])

    def test_unknown_policy_raises(self) -> None:
        setup = dict(DOC_EXAMPLE)
        setup["policy"] = "MRU"
        with self.assertRaises(ValueError):
            CacheSimulator().run(setup)

    def test_associativity_must_divide_size(self) -> None:
        setup = dict(DOC_EXAMPLE)
        setup["associativity"] = 3  # 4 lines / 3-way is not a whole set count
        with self.assertRaises(ValueError):
            CacheSimulator().run(setup)


if __name__ == "__main__":
    unittest.main()
