#!/usr/bin/env python3
"""
ABOUTME: Simulators must reject absurd setups instead of allocating forever.
ABOUTME: Validation runs author input, so an unbounded scalar is a hang.
"""

import unittest

from computerquest.mechanics.simulators.cache import CacheSimulator
from computerquest.mechanics.simulators.pipeline import PipelineSimulator
from computerquest.mechanics.simulators.storage import SeekDistanceSimulator
from computerquest.mechanics.simulators.tlb import TLBSimulator, TLBTranslateSimulator

# Shipped content is tiny: size_lines 4, accesses 10, requests 4, instructions 4,
# tlb_entries 2. The bounds below sit orders of magnitude above that, so they
# constrain only inputs no real puzzle would ever carry.


class TestCacheBounds(unittest.TestCase):
    """`size_lines` sizes a list comprehension, so one integer decides how much
    memory the process asks for. 10**9 exhausts a gigabyte in about five
    seconds; unbounded it runs to the OOM killer."""

    def setUp(self):
        self.sim = CacheSimulator()

    def _setup(self, **over):
        base = dict(policy="LRU", size_lines=4, line_size_bytes=64,
                    associativity=1, accesses=[0, 64, 128])
        base.update(over)
        return base

    def test_baseline_setup_still_runs(self):
        self.assertEqual(len(self.sim.run(self._setup())), 3)

    def test_absurd_size_lines_is_rejected(self):
        with self.assertRaises(ValueError):
            self.sim.run(self._setup(size_lines=100_000))

    def test_absurd_line_size_is_rejected(self):
        with self.assertRaises(ValueError):
            self.sim.run(self._setup(line_size_bytes=10_000_000))

    def test_absurd_trace_length_is_rejected(self):
        with self.assertRaises(ValueError):
            self.sim.run(self._setup(accesses=list(range(5_000))))

    def test_generous_but_sane_setup_is_accepted(self):
        """The bound must not squeeze legitimate authoring room."""
        result = self.sim.run(self._setup(size_lines=256, associativity=1,
                                          accesses=list(range(512))))
        self.assertEqual(len(result), 512)


class TestStorageBounds(unittest.TestCase):
    """SSTF is quadratic: `min` then `remove`, both O(n), inside a loop of n.
    Measured 0.15s at n=2000 and 2.97s at n=8000."""

    def setUp(self):
        self.sim = SeekDistanceSimulator()

    def test_baseline_setup_still_runs(self):
        self.assertEqual(
            self.sim.run({"algorithm": "FCFS", "start_track": 50, "requests": [60, 40]}),
            30,
        )

    def test_absurd_request_count_is_rejected(self):
        with self.assertRaises(ValueError):
            self.sim.run({"algorithm": "SSTF", "start_track": 0,
                          "requests": list(range(5_000))})

    def test_generous_request_count_is_accepted(self):
        self.assertIsInstance(
            self.sim.run({"algorithm": "SSTF", "start_track": 0,
                          "requests": list(range(256))}),
            int,
        )


class TestPipelineBounds(unittest.TestCase):
    def setUp(self):
        self.sim = PipelineSimulator()

    def test_absurd_instruction_count_is_rejected(self):
        instructions = [["ADD", ["R1"], "R2"]] * 5_000
        with self.assertRaises(ValueError):
            self.sim.run({"stages": 5, "forwarding": True, "instructions": instructions})

    def test_generous_instruction_count_is_accepted(self):
        instructions = [["ADD", ["R1"], "R2"]] * 256
        self.assertIsInstance(
            self.sim.run({"stages": 5, "forwarding": True, "instructions": instructions}),
            int,
        )


class TestTLBBounds(unittest.TestCase):
    """`tlb_entries <= 0` currently fails only by an incidental IndexError from
    popping an empty list, and `page_size = 0` by ZeroDivisionError. Both should
    say what is wrong."""

    def test_zero_tlb_entries_is_rejected_clearly(self):
        with self.assertRaises(ValueError):
            TLBSimulator().run({"page_size": 4096, "tlb_entries": 0, "policy": "LRU",
                                "page_table": {0: 1}, "accesses": [0]})

    def test_negative_tlb_entries_is_rejected_clearly(self):
        with self.assertRaises(ValueError):
            TLBSimulator().run({"page_size": 4096, "tlb_entries": -5, "policy": "LRU",
                                "page_table": {0: 1}, "accesses": [0]})

    def test_zero_page_size_is_rejected_clearly(self):
        with self.assertRaises(ValueError):
            TLBTranslateSimulator().run({"page_size": 0, "page_table": {0: 1},
                                         "vaddr": 0})

    def test_absurd_tlb_entries_is_rejected(self):
        with self.assertRaises(ValueError):
            TLBSimulator().run({"page_size": 4096, "tlb_entries": 100_000,
                                "policy": "LRU", "page_table": {0: 1}, "accesses": [0]})

    def test_baseline_tlb_setups_still_run(self):
        out = TLBSimulator().run({"page_size": 4096, "tlb_entries": 2, "policy": "LRU",
                                  "page_table": {0: 1, 1: 2}, "accesses": [0, 4096, 0]})
        self.assertEqual(len(out), 3)
        self.assertEqual(
            TLBTranslateSimulator().run({"page_size": 4096, "page_table": {0: 5},
                                         "vaddr": 0x100}),
            5 * 4096 + 0x100,
        )


class TestShippedContentUnaffected(unittest.TestCase):
    def test_every_shipped_puzzle_still_validates(self):
        """The bounds must be invisible to real content: load_registry runs every
        shipped setup through its simulator."""
        from computerquest.mechanics.puzzles import load_registry

        # load_registry runs every shipped setup through its simulator, so a
        # bound that caught real content would raise here. The exact count is
        # pinned by the golden-answer fixture, not duplicated in this test.
        self.assertGreater(len(load_registry().by_id), 0)


if __name__ == "__main__":
    unittest.main()
