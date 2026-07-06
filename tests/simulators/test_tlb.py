#!/usr/bin/env python3
"""
ABOUTME: Tests for the TLB simulator, hit/miss mode and translate mode.
ABOUTME: Expectations hand-derived from the textbook x86 single-level paging model.
"""

import unittest

from computerquest.mechanics.simulators.tlb import TLBSimulator, TLBTranslateSimulator

# 4 KB pages, 2-entry fully-associative TLB, LRU. Virtual addresses touch
# VPNs 0, 1, 0, 3, 1: with two entries, VPN 0 hits on re-touch, VPN 3
# evicts VPN 1 (LRU order after the hit is [1, 0]), so the final access to
# VPN 1 misses again.
HITMISS_SETUP = {
    "page_size": 4096,
    "tlb_entries": 2,
    "policy": "LRU",
    "page_table": {0: 8, 1: 9, 3: 2},
    "accesses": [0x0000, 0x1000, 0x0004, 0x3000, 0x1004],
}


class TestTLBHitMiss(unittest.TestCase):
    def test_lru_sequence(self) -> None:
        self.assertEqual(
            TLBSimulator().run(HITMISS_SETUP), ["M", "M", "H", "M", "M"]
        )

    def test_fifo_differs_from_lru(self) -> None:
        """With FIFO, the VPN-0 hit does not refresh recency: VPN 3 evicts
        VPN 0 (oldest by insertion), so the final VPN-1 access hits."""
        setup = dict(HITMISS_SETUP)
        setup["policy"] = "FIFO"
        self.assertEqual(
            TLBSimulator().run(setup), ["M", "M", "H", "M", "H"]
        )

    def test_unmapped_vpn_raises(self) -> None:
        setup = dict(HITMISS_SETUP)
        setup["accesses"] = [0x9000]  # VPN 9 not in the page table
        with self.assertRaises(ValueError):
            TLBSimulator().run(setup)


class TestTLBTranslate(unittest.TestCase):
    def test_translation_math(self) -> None:
        """VPN 1 maps to PFN 9: 0x1234 -> 9 * 4096 + 0x234 = 0x9234."""
        setup = {
            "page_size": 4096,
            "page_table": {0: 5, 1: 9},
            "vaddr": 0x1234,
        }
        self.assertEqual(TLBTranslateSimulator().run(setup), 0x9234)

    def test_offset_zero(self) -> None:
        setup = {"page_size": 4096, "page_table": {2: 7}, "vaddr": 0x2000}
        self.assertEqual(TLBTranslateSimulator().run(setup), 7 * 4096)

    def test_unmapped_raises(self) -> None:
        setup = {"page_size": 4096, "page_table": {0: 5}, "vaddr": 0x5000}
        with self.assertRaises(ValueError):
            TLBTranslateSimulator().run(setup)


if __name__ == "__main__":
    unittest.main()
