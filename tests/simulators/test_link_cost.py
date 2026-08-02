#!/usr/bin/env python3
"""
ABOUTME: Tests for the link-cost simulator (PRD 1 Feature B item 4).
ABOUTME: All expectations hand-derived before implementation.
"""

import unittest

from computerquest.mechanics.simulators.link import LinkCostSimulator

# Three equal links: 1000 units of payload at 100 units/tick is 10 ticks of
# transmission per hop, plus 2 ticks of latency on each.
EQUAL = [
    {"latency": 2, "bandwidth": 100},
    {"latency": 2, "bandwidth": 100},
    {"latency": 2, "bandwidth": 100},
]


class TestStoreAndForward(unittest.TestCase):
    def test_each_hop_pays_the_whole_transmission(self) -> None:
        """3 * 10 transmission + 3 * 2 latency = 36."""
        setup = {"size": 1000, "links": EQUAL, "mode": "store_and_forward"}
        self.assertEqual(LinkCostSimulator().run(setup), 36)

    def test_a_single_link_is_transmission_plus_latency(self) -> None:
        setup = {"size": 1000, "links": EQUAL[:1], "mode": "store_and_forward"}
        self.assertEqual(LinkCostSimulator().run(setup), 12)


class TestCutThrough(unittest.TestCase):
    def test_only_the_slowest_hop_pays_transmission(self) -> None:
        """Forwarding starts before the message has fully arrived, so the
        transmission cost is paid once at the bottleneck: 10 + 6 = 16."""
        setup = {"size": 1000, "links": EQUAL, "mode": "cut_through"}
        self.assertEqual(LinkCostSimulator().run(setup), 16)

    def test_the_bottleneck_link_sets_the_transmission_cost(self) -> None:
        """A 50-unit/tick link in the middle costs 20 ticks and dominates."""
        links = [
            {"latency": 1, "bandwidth": 100},
            {"latency": 1, "bandwidth": 50},
            {"latency": 1, "bandwidth": 100},
        ]
        setup = {"size": 1000, "links": links, "mode": "cut_through"}
        self.assertEqual(LinkCostSimulator().run(setup), 23)

    def test_one_link_costs_the_same_either_way(self) -> None:
        """With a single hop there is nothing to overlap, so the knob does
        nothing. A puzzle built on this device needs at least two hops."""
        for mode in ("store_and_forward", "cut_through"):
            setup = {"size": 1000, "links": EQUAL[:1], "mode": mode}
            with self.subTest(mode=mode):
                self.assertEqual(LinkCostSimulator().run(setup), 12)


class TestTheKnobIsReal(unittest.TestCase):
    """Every other simulator has a policy knob whose flip changes the answer on
    an identical workload. That is the whole reason this simulator exists."""

    def test_cut_through_is_never_slower(self) -> None:
        cases = ([EQUAL, 1000], [EQUAL[:2], 500], [EQUAL, 100])
        for links, size in cases:
            saf = LinkCostSimulator().run(
                {"size": size, "links": links, "mode": "store_and_forward"}
            )
            cut = LinkCostSimulator().run(
                {"size": size, "links": links, "mode": "cut_through"}
            )
            with self.subTest(size=size, hops=len(links)):
                self.assertLessEqual(cut, saf)

    def test_the_gap_widens_with_hop_count(self) -> None:
        """This is the pipelining lesson again: more stages, more to overlap."""
        def gap(hops):
            links = EQUAL[:1] * hops
            saf = LinkCostSimulator().run(
                {"size": 1000, "links": links, "mode": "store_and_forward"}
            )
            cut = LinkCostSimulator().run(
                {"size": 1000, "links": links, "mode": "cut_through"}
            )
            return saf - cut

        self.assertEqual(gap(1), 0)
        self.assertLess(gap(2), gap(3))


class TestAuthorErrors(unittest.TestCase):
    def test_an_indivisible_size_is_rejected(self) -> None:
        """A fractional answer cannot be typed, so it is an author error rather
        than something to round and hope the player guesses the same way."""
        setup = {
            "size": 1001,
            "links": [{"latency": 1, "bandwidth": 100}],
            "mode": "cut_through",
        }
        with self.assertRaises(ValueError):
            LinkCostSimulator().run(setup)

    def test_an_unknown_mode_is_rejected(self) -> None:
        setup = {"size": 1000, "links": EQUAL, "mode": "wormhole"}
        with self.assertRaises(ValueError):
            LinkCostSimulator().run(setup)

    def test_zero_bandwidth_is_rejected(self) -> None:
        setup = {
            "size": 1000,
            "links": [{"latency": 1, "bandwidth": 0}],
            "mode": "cut_through",
        }
        with self.assertRaises(ValueError):
            LinkCostSimulator().run(setup)

    def test_an_empty_path_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LinkCostSimulator().run({"size": 1000, "links": [], "mode": "cut_through"})

    def test_an_absurd_hop_count_is_rejected(self) -> None:
        links = [{"latency": 1, "bandwidth": 100}] * 100_000
        setup = {"size": 1000, "links": links, "mode": "cut_through"}
        with self.assertRaises(ValueError):
            LinkCostSimulator().run(setup)


if __name__ == "__main__":
    unittest.main()
