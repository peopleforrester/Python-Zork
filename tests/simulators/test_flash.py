#!/usr/bin/env python3
"""
ABOUTME: Tests for the flash simulator (issue #1: the SSD room had no flash lesson).
ABOUTME: All expectations hand-derived before implementation.
"""

import unittest

from computerquest.mechanics.simulators.flash import FlashWriteSimulator

# A block of 4 pages. Rewriting one page is where the whole lesson lives.
BLOCK = {"pages_per_block": 4, "page_size": 1}


class TestInPlacePolicy(unittest.TestCase):
    """The policy a hard disk can use and flash cannot: overwrite where it sits."""

    def test_one_page_costs_one_page_write(self) -> None:
        setup = {**BLOCK, "policy": "in_place", "writes": [0]}
        self.assertEqual(FlashWriteSimulator().run(setup), 1)

    def test_rewriting_the_same_page_still_costs_one_each_time(self) -> None:
        setup = {**BLOCK, "policy": "in_place", "writes": [0, 0, 0]}
        self.assertEqual(FlashWriteSimulator().run(setup), 3)


class TestEraseBlockPolicy(unittest.TestCase):
    """What flash actually does: a page cannot be overwritten, so rewriting one
    page means copying its whole block elsewhere."""

    def test_a_first_write_to_a_clean_page_costs_one(self) -> None:
        """No copy is needed until a page has to be rewritten."""
        setup = {**BLOCK, "policy": "erase_block", "writes": [0]}
        self.assertEqual(FlashWriteSimulator().run(setup), 1)

    def test_rewriting_a_page_rewrites_its_whole_block(self) -> None:
        """Page 0 written, then written again: the second costs a copy of all
        4 pages. 1 + 4 = 5 page-writes for 2 pages of user data."""
        setup = {**BLOCK, "policy": "erase_block", "writes": [0, 0]}
        self.assertEqual(FlashWriteSimulator().run(setup), 5)

    def test_writing_four_clean_pages_costs_four(self) -> None:
        setup = {**BLOCK, "policy": "erase_block", "writes": [0, 1, 2, 3]}
        self.assertEqual(FlashWriteSimulator().run(setup), 4)

    def test_a_fifth_write_to_a_full_block_pays_the_copy(self) -> None:
        """4 clean writes, then a rewrite of page 0: 4 + 4 = 8."""
        setup = {**BLOCK, "policy": "erase_block", "writes": [0, 1, 2, 3, 0]}
        self.assertEqual(FlashWriteSimulator().run(setup), 8)

    def test_pages_in_different_blocks_do_not_interfere(self) -> None:
        """Page 4 lives in block 1, so rewriting page 0 copies block 0 only."""
        setup = {**BLOCK, "policy": "erase_block", "writes": [0, 4, 0]}
        self.assertEqual(FlashWriteSimulator().run(setup), 1 + 1 + 4)


class TestTheKnobIsReal(unittest.TestCase):
    """Every simulator carries a setting whose flip changes the answer on a
    byte-identical setup. That is what write amplification is."""

    def test_the_two_policies_disagree_on_a_rewrite(self) -> None:
        writes = {**BLOCK, "writes": [0, 1, 2, 3, 0]}
        in_place = FlashWriteSimulator().run({**writes, "policy": "in_place"})
        erase = FlashWriteSimulator().run({**writes, "policy": "erase_block"})
        self.assertLess(in_place, erase)

    def test_they_agree_when_nothing_is_ever_rewritten(self) -> None:
        """A pure append workload has no amplification, which is why
        sequential writes are kind to flash."""
        writes = {**BLOCK, "writes": [0, 1, 2, 3]}
        self.assertEqual(
            FlashWriteSimulator().run({**writes, "policy": "in_place"}),
            FlashWriteSimulator().run({**writes, "policy": "erase_block"}),
        )

    def test_a_bigger_block_amplifies_a_rewrite_more(self) -> None:
        small = FlashWriteSimulator().run(
            {"pages_per_block": 2, "policy": "erase_block", "writes": [0, 0]}
        )
        large = FlashWriteSimulator().run(
            {"pages_per_block": 8, "policy": "erase_block", "writes": [0, 0]}
        )
        self.assertLess(small, large)


class TestAuthorErrors(unittest.TestCase):
    def test_an_unknown_policy_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FlashWriteSimulator().run({**BLOCK, "policy": "trim", "writes": [0]})

    def test_a_zero_page_block_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FlashWriteSimulator().run(
                {"pages_per_block": 0, "policy": "in_place", "writes": [0]}
            )

    def test_an_empty_workload_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FlashWriteSimulator().run({**BLOCK, "policy": "in_place", "writes": []})

    def test_a_negative_page_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FlashWriteSimulator().run({**BLOCK, "policy": "in_place", "writes": [-1]})

    def test_an_absurd_workload_is_rejected(self) -> None:
        setup = {**BLOCK, "policy": "erase_block", "writes": list(range(100_000))}
        with self.assertRaises(ValueError):
            FlashWriteSimulator().run(setup)


if __name__ == "__main__":
    unittest.main()
