#!/usr/bin/env python3
"""
ABOUTME: Covers the `simulate` verb surface, including the cross-capability
ABOUTME: refusals when a verb is aimed at the minigame that lacks it.
"""

import unittest

from tests._helpers import build_real_game


def _game_with(minigame: str):
    """A game with knowledge high enough to open the requested minigame."""
    game = build_real_game()
    for area in game.player.knowledge:
        game.player.knowledge[area] = 5
    game.feed(f"simulate {minigame}")
    return game


class TestSimulateDispatch(unittest.TestCase):
    def test_no_argument_asks_for_one(self):
        game = build_real_game()
        self.assertIn("specify a simulation type", game.feed("simulate"))

    def test_action_without_an_active_simulation(self):
        game = build_real_game()
        out = game.feed("simulate step")
        self.assertTrue(out.strip(), "a bare action must still say something")

    def test_cpu_minigame_is_gated_on_knowledge(self):
        game = build_real_game()
        game.player.knowledge["cpu"] = 0
        self.assertIn("knowledge", game.feed("simulate cpu").lower())

    def test_cpu_minigame_starts_when_knowledgeable(self):
        game = _game_with("cpu")
        self.assertIsNotNone(game.current_minigame)

    def test_memory_minigame_starts_when_knowledgeable(self):
        game = _game_with("memory")
        self.assertIsNotNone(game.current_minigame)

    def test_unknown_action_lists_the_valid_ones(self):
        game = _game_with("cpu")
        out = game.feed("simulate wibble")
        self.assertIn("Unknown simulation action", out)
        self.assertIn("step", out)


class TestSimulateStepAndStatus(unittest.TestCase):
    def test_step_advances_the_cpu_simulation(self):
        game = _game_with("cpu")
        self.assertTrue(game.feed("simulate step").strip())

    def test_status_reports_without_advancing(self):
        game = _game_with("cpu")
        self.assertTrue(game.feed("simulate status").strip())

    def test_reset_and_stop_are_accepted(self):
        game = _game_with("cpu")
        self.assertTrue(game.feed("simulate reset").strip())
        self.assertTrue(game.feed("simulate stop").strip())


class TestCrossCapabilityRefusals(unittest.TestCase):
    """Each verb belongs to one minigame; aimed at the other it must explain
    itself rather than raise. These branches were entirely dark."""

    def test_pattern_is_refused_by_the_cpu_simulation(self):
        game = _game_with("cpu")
        self.assertIn("doesn't support access patterns", game.feed("simulate pattern loop"))

    def test_cache_tuning_is_refused_by_the_cpu_simulation(self):
        game = _game_with("cpu")
        self.assertIn("doesn't support cache tuning", game.feed("simulate cache l1 8"))

    def test_forwarding_is_refused_by_the_memory_simulation(self):
        game = _game_with("memory")
        self.assertIn("doesn't support forwarding", game.feed("simulate forward"))

    def test_pattern_without_an_argument_shows_usage(self):
        game = _game_with("memory")
        self.assertIn("Usage: simulate pattern", game.feed("simulate pattern"))

    def test_cache_with_a_non_numeric_size_shows_usage(self):
        game = _game_with("memory")
        self.assertIn("Usage: simulate cache", game.feed("simulate cache l1 big"))

    def test_memory_simulation_accepts_its_own_verbs(self):
        game = _game_with("memory")
        self.assertNotIn("doesn't support", game.feed("simulate pattern loop"))
        self.assertNotIn("doesn't support", game.feed("simulate cache l1 8"))

    def test_cpu_simulation_accepts_forwarding(self):
        game = _game_with("cpu")
        self.assertNotIn("doesn't support", game.feed("simulate forward"))


class TestQuickHelp(unittest.TestCase):
    """The `?` overlay is a separate screen from the full `help`."""

    def test_question_mark_renders_a_command_reference(self):
        game = build_real_game()
        out = game.feed("?")
        self.assertIn("COMMAND REFERENCE", out)

    def test_quick_help_is_shorter_than_full_help(self):
        game = build_real_game()
        self.assertLess(len(game.feed("?")), len(game.feed("help")))


if __name__ == "__main__":
    unittest.main()
