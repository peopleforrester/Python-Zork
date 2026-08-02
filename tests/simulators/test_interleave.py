#!/usr/bin/env python3
"""
ABOUTME: Tests for the channel-interleave simulator (issue #3).
ABOUTME: All expectations hand-derived before implementation.
"""

import unittest

from computerquest.mechanics.simulators.interleave import ChannelInterleaveSimulator

# Four channels, each able to serve one line per cycle.
FOUR = {"channels": 4, "lines_per_channel_cycle": 1}


class TestBlockMapping(unittest.TestCase):
    """Each channel owns a contiguous address range, so a sequential burst
    lands entirely inside one of them and serialises."""

    def test_a_sequential_burst_hits_one_channel(self) -> None:
        """8 consecutive lines, block size 8, so all 8 land on channel 0 and
        that channel serves them one per cycle."""
        setup = {**FOUR, "mapping": "block", "block_lines": 8, "lines": [0, 1, 2, 3, 4, 5, 6, 7]}
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 8)

    def test_a_burst_spanning_two_blocks_uses_two_channels(self) -> None:
        """Lines 6..9 with block size 8: 6,7 on channel 0 and 8,9 on channel 1,
        so the busiest channel serves 2 and they overlap."""
        setup = {**FOUR, "mapping": "block", "block_lines": 8, "lines": [6, 7, 8, 9]}
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 2)


class TestInterleavedMapping(unittest.TestCase):
    """Consecutive lines round-robin across channels, so a sequential burst
    spreads and the channels work in parallel."""

    def test_a_sequential_burst_spreads_across_every_channel(self) -> None:
        """8 consecutive lines over 4 channels: 2 each, all in parallel."""
        setup = {**FOUR, "mapping": "interleaved", "lines": [0, 1, 2, 3, 4, 5, 6, 7]}
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 2)

    def test_a_stride_that_matches_the_channel_count_defeats_it(self) -> None:
        """Every 4th line is the same channel, so an interleaved mapping is
        no better than a block one. This is the pathological stride."""
        setup = {**FOUR, "mapping": "interleaved", "lines": [0, 4, 8, 12]}
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 4)

    def test_one_line_costs_one_cycle(self) -> None:
        setup = {**FOUR, "mapping": "interleaved", "lines": [0]}
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 1)


class TestChannelWidth(unittest.TestCase):
    def test_a_wider_channel_serves_more_lines_per_cycle(self) -> None:
        setup = {
            "channels": 1, "lines_per_channel_cycle": 2,
            "mapping": "interleaved", "lines": [0, 1, 2, 3],
        }
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 2)

    def test_a_partial_cycle_still_costs_a_whole_one(self) -> None:
        setup = {
            "channels": 1, "lines_per_channel_cycle": 2,
            "mapping": "interleaved", "lines": [0, 1, 2],
        }
        self.assertEqual(ChannelInterleaveSimulator().run(setup), 2)


class TestTheKnobIsReal(unittest.TestCase):
    def test_interleaving_never_loses_on_a_sequential_burst(self) -> None:
        lines = list(range(16))
        block = ChannelInterleaveSimulator().run(
            {**FOUR, "mapping": "block", "block_lines": 16, "lines": lines}
        )
        inter = ChannelInterleaveSimulator().run(
            {**FOUR, "mapping": "interleaved", "lines": lines}
        )
        self.assertLess(inter, block)

    def test_more_channels_help_only_when_the_access_pattern_spreads(self) -> None:
        stride = [0, 4, 8, 12]
        four = ChannelInterleaveSimulator().run({**FOUR, "mapping": "interleaved", "lines": stride})
        eight = ChannelInterleaveSimulator().run(
            {"channels": 8, "lines_per_channel_cycle": 1, "mapping": "interleaved", "lines": stride}
        )
        # 8 channels does help this stride, because 4 no longer divides it.
        self.assertLess(eight, four)


class TestAuthorErrors(unittest.TestCase):
    def test_an_unknown_mapping_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChannelInterleaveSimulator().run({**FOUR, "mapping": "hashed", "lines": [0]})

    def test_zero_channels_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChannelInterleaveSimulator().run(
                {"channels": 0, "lines_per_channel_cycle": 1, "mapping": "block",
                 "block_lines": 4, "lines": [0]}
            )

    def test_block_mapping_needs_a_block_size(self) -> None:
        with self.assertRaises(ValueError):
            ChannelInterleaveSimulator().run({**FOUR, "mapping": "block", "lines": [0]})

    def test_an_empty_burst_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChannelInterleaveSimulator().run({**FOUR, "mapping": "interleaved", "lines": []})

    def test_an_absurd_burst_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChannelInterleaveSimulator().run(
                {**FOUR, "mapping": "interleaved", "lines": list(range(100_000))}
            )


if __name__ == "__main__":
    unittest.main()
