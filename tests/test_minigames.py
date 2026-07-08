#!/usr/bin/env python3
"""
ABOUTME: Tests for the simulator-backed CPU and memory minigames (microquiz step 7).
ABOUTME: Cycle/hit counts are the simulator's, not hand numbers; minigames delegate.
"""

import unittest

from computerquest.mechanics.minigames import CPUPipelineMinigame, MemoryHierarchyMinigame
from computerquest.mechanics.minigames.cpu_workload import WORKLOAD
from computerquest.mechanics.minigames.memory_patterns import PATTERNS
from tests._helpers import build_real_game


def run_to_finish(mini, max_steps=200):
    steps = 0
    while not mini.is_finished() and steps < max_steps:
        mini.step()
        steps += 1
    return steps


class TestCPUMinigame(unittest.TestCase):
    def setUp(self):
        self.game = build_real_game()
        self.game.player.knowledge["cpu"] = 3  # meet the gate

    def make(self):
        return CPUPipelineMinigame(self.game)

    def test_default_is_pipelined_stalls_no_forwarding(self):
        mini = self.make()
        self.assertTrue(mini.pipelined)
        self.assertFalse(mini.forwarding)

    def test_pipelined_with_stalls_finishes_at_simulator_total(self):
        mini = self.make()  # forwarding off
        run_to_finish(mini)
        self.assertTrue(mini.is_finished())
        self.assertEqual(mini.total_cycles(), 16)

    def test_forwarding_reduces_cycle_count(self):
        mini = self.make()
        mini.toggle_forwarding()
        self.assertTrue(mini.forwarding)
        run_to_finish(mini)
        self.assertEqual(mini.total_cycles(), 12)

    def test_non_pipelined_is_five_stages_per_instruction(self):
        mini = self.make()
        mini.toggle_pipeline()
        self.assertFalse(mini.pipelined)
        run_to_finish(mini)
        self.assertEqual(mini.total_cycles(), len(WORKLOAD) * 5)

    def test_toggle_restarts_at_cycle_zero(self):
        mini = self.make()
        mini.step()
        mini.step()
        mini.toggle_pipeline()
        self.assertEqual(mini.cycle, 0)

    def test_status_does_not_advance(self):
        mini = self.make()
        mini.step()
        c = mini.cycle
        mini.get_status()
        self.assertEqual(mini.cycle, c)

    def test_debrief_reports_stall_count(self):
        mini = self.make()  # no forwarding: 6 stall cycles across the workload
        run_to_finish(mini)
        debrief = mini.get_status()
        self.assertIn("16", debrief)
        self.assertIn("stall", debrief.lower())


class TestMemoryMinigame(unittest.TestCase):
    def setUp(self):
        self.game = build_real_game()
        self.game.player.knowledge["memory"] = 3

    def make(self):
        return MemoryHierarchyMinigame(self.game)

    def test_patterns_have_distinct_ordered_hit_rates(self):
        rates = {}
        for name in ("loop", "sequential", "random", "stride"):
            mini = self.make()
            mini.set_pattern(name)
            run_to_finish(mini)
            rates[name] = mini.hit_rate()
        self.assertGreater(rates["loop"], rates["sequential"])
        self.assertGreater(rates["sequential"], rates["random"])
        self.assertGreater(rates["random"], rates["stride"])
        self.assertEqual(rates["stride"], 0.0)

    def test_exact_hit_counts_match_simulator(self):
        expected = {"sequential": 12, "loop": 15, "stride": 0, "random": 3}
        for name, want in expected.items():
            mini = self.make()
            mini.set_pattern(name)
            run_to_finish(mini)
            self.assertEqual(mini.hits, want, name)

    def test_step_reports_hit_or_miss(self):
        mini = self.make()
        mini.set_pattern("loop")
        first = mini.step()
        self.assertIn("MISS", first.upper())  # cold cache

    def test_reset_preserves_pattern(self):
        mini = self.make()
        mini.set_pattern("stride")
        run_to_finish(mini)
        mini.reset()
        self.assertEqual(mini.pattern_name, "stride")
        self.assertEqual(mini.cursor, 0)

    def test_unknown_pattern_rejected(self):
        mini = self.make()
        msg = mini.set_pattern("bogus")
        self.assertIn("unknown", msg.lower())
        self.assertNotEqual(mini.pattern_name, "bogus")


class TestMinigameGatesAndFeed(unittest.TestCase):
    """Gate behavior and the full feed() path with ENABLE_MINIGAMES on."""

    def setUp(self):
        self.game = build_real_game()

    def test_cpu_gate_blocks_below_three(self):
        self.game.player.knowledge["cpu"] = 2
        out = self.game.feed("simulate cpu")
        self.assertIn("knowledge", out.lower())
        self.assertIsNone(self.game.current_minigame)

    def test_cpu_starts_at_three(self):
        self.game.player.knowledge["cpu"] = 3
        out = self.game.feed("simulate cpu")
        self.assertIsNotNone(self.game.current_minigame)
        self.assertIn("pipeline", out.lower())

    def test_memory_tuning_gated_by_four(self):
        self.game.player.knowledge["memory"] = 3
        self.game.feed("simulate memory")
        out = self.game.feed("simulate cache l1 8")
        self.assertIn("knowledge", out.lower())

    def test_stop_clears_active_minigame(self):
        self.game.player.knowledge["cpu"] = 3
        self.game.feed("simulate cpu")
        self.game.feed("simulate stop")
        self.assertIsNone(self.game.current_minigame)

    def test_pattern_names_available(self):
        self.assertEqual(
            set(PATTERNS), {"sequential", "loop", "stride", "random"}
        )


if __name__ == "__main__":
    unittest.main()
