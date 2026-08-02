#!/usr/bin/env python3
"""
ABOUTME: Tests for the SIMD warp simulator (issue #2: the GPU taught nothing).
ABOUTME: All expectations hand-derived before implementation.
"""

import unittest

from computerquest.mechanics.simulators.simd import WarpDivergenceSimulator

# A warp of 4 lanes over a branch whose two sides cost different amounts.
WARP = {"lanes": 4, "then_cost": 6, "else_cost": 2}


class TestUniformBranch(unittest.TestCase):
    """Every lane agrees, so the warp runs one side and the other is free."""

    def test_all_lanes_take_the_then_side(self) -> None:
        setup = {**WARP, "taken": [True, True, True, True]}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 6)

    def test_all_lanes_take_the_else_side(self) -> None:
        setup = {**WARP, "taken": [False, False, False, False]}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 2)


class TestDivergentBranch(unittest.TestCase):
    """Lanes disagree, so the hardware runs BOTH sides with the inactive lanes
    masked off. The warp pays the sum, not the max."""

    def test_a_single_disagreeing_lane_costs_the_full_other_side(self) -> None:
        setup = {**WARP, "taken": [True, True, True, False]}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 8)

    def test_an_even_split_costs_the_same_as_one_odd_lane(self) -> None:
        """The count of disagreeing lanes does not matter, only that they
        disagree at all. That is the counter-intuitive part."""
        setup = {**WARP, "taken": [True, True, False, False]}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 8)

    def test_divergence_never_beats_agreement(self) -> None:
        uniform = WarpDivergenceSimulator().run({**WARP, "taken": [True] * 4})
        diverged = WarpDivergenceSimulator().run(
            {**WARP, "taken": [True, True, True, False]}
        )
        self.assertGreater(diverged, uniform)


class TestWarpBoundary(unittest.TestCase):
    """Lanes in different warps never diverge against each other, which is why
    sorting work by branch outcome is the standard fix."""

    def test_two_warps_each_uniform_pay_only_their_own_side(self) -> None:
        """8 lanes over a warp of 4: the first warp is all-then (6), the
        second all-else (2). Total 8, with no divergence anywhere."""
        setup = {**WARP, "taken": [True] * 4 + [False] * 4}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 8)

    def test_the_same_lanes_shuffled_across_warps_diverge_twice(self) -> None:
        """Identical work, identical counts, interleaved instead of sorted:
        both warps now diverge and each pays both sides. 8 + 8 = 16."""
        setup = {**WARP, "taken": [True, False] * 4}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 16)

    def test_a_partial_final_warp_still_counts(self) -> None:
        setup = {**WARP, "taken": [True] * 4 + [False]}
        self.assertEqual(WarpDivergenceSimulator().run(setup), 6 + 2)


class TestAuthorErrors(unittest.TestCase):
    def test_zero_lanes_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WarpDivergenceSimulator().run({**WARP, "lanes": 0, "taken": [True]})

    def test_an_empty_workload_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WarpDivergenceSimulator().run({**WARP, "taken": []})

    def test_a_negative_cost_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WarpDivergenceSimulator().run({**WARP, "then_cost": -1, "taken": [True]})

    def test_an_absurd_lane_count_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WarpDivergenceSimulator().run(
                {**WARP, "taken": [True] * 100_000}
            )


if __name__ == "__main__":
    unittest.main()
