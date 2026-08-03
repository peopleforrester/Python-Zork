#!/usr/bin/env python3
"""
ABOUTME: Covers game.py's CLI surface: the REPL, readline setup, completions.
ABOUTME: The web build never runs these, so nothing else exercised them.
"""

import builtins
import io
import sys
import unittest
import unittest.mock

from tests._helpers import build_real_game


class TestCompletionPools(unittest.TestCase):
    """`completions` picks a candidate pool per verb. Most branches had no
    test, and the one that did have a bug (solve offering gated ids) proved
    these matter."""

    def setUp(self):
        self.game = build_real_game()

    def test_quarantine_offers_only_found_viruses(self):
        self.game.player.found_viruses = ["boot_sector_virus", "rootkit_virus"]
        self.assertEqual(
            self.game.completions("quarantine "),
            ["boot_sector_virus", "rootkit_virus"],
        )

    def test_quarantine_offers_nothing_before_anything_is_found(self):
        self.assertEqual(self.game.completions("quarantine "), [])

    def test_about_offers_the_component_topics(self):
        from computerquest.content import COMPONENT_TOPICS

        self.assertEqual(self.game.completions("about "), sorted(COMPONENT_TOPICS))

    def test_help_offers_every_command(self):
        offered = self.game.completions("help ")
        self.assertEqual(offered, sorted(self.game.command_processor.commands))

    def test_h_is_an_alias_for_help_completion(self):
        self.assertEqual(self.game.completions("h "), self.game.completions("help "))

    def test_go_offers_directions_not_commands(self):
        offered = self.game.completions("go ")
        self.assertEqual(offered, sorted(self.game.command_processor.direction_words))
        self.assertNotIn("look", offered)

    def test_move_offers_the_same_as_go(self):
        self.assertEqual(self.game.completions("move "), self.game.completions("go "))

    def test_an_unknown_verb_falls_back_to_things_you_can_touch(self):
        """Room contents plus inventory, which is what most verbs act on."""
        self.game.player.items = {"decoder_tool": "a tool"}
        offered = self.game.completions("examine ")
        self.assertIn("decoder_tool", offered)
        for item in self.game.player.location.items:
            self.assertIn(item, offered)

    def test_a_prefix_filters_the_pool(self):
        self.game.player.found_viruses = ["boot_sector_virus", "rootkit_virus"]
        self.assertEqual(self.game.completions("quarantine root"), ["rootkit_virus"])

    def test_results_are_sorted_and_deduplicated(self):
        """The pool concatenates two collections, so an item held in the room
        and in the pack would otherwise appear twice."""
        item = next(iter(self.game.player.location.items))
        self.game.player.items = {item: "same name"}
        offered = self.game.completions("examine ")
        self.assertEqual(len(offered), len(set(offered)))
        self.assertEqual(offered, sorted(offered))


class TestTechnicalDetailsOnRevisit(unittest.TestCase):
    """A visited component reveals its technical readout. The block building
    it had no coverage, so the readout could vanish silently."""

    def _look_at_a_visited_room(self, **attrs):
        game = build_real_game()
        room = game.player.location
        room.mark_visited()
        for key, value in attrs.items():
            setattr(room, key, value)
        return game.feed("look")

    def test_security_level_is_reported(self):
        self.assertIn("Security Level: 3", self._look_at_a_visited_room(security_level=3))

    def test_data_types_are_reported(self):
        out = self._look_at_a_visited_room(data_types=["instructions", "operands"])
        self.assertIn("instructions", out)

    def test_performance_metrics_are_reported(self):
        out = self._look_at_a_visited_room(performance={"speed": 9, "capacity": 0})
        self.assertIn("Performance Metrics:", out)
        self.assertIn("Speed", out)

    def test_a_zero_metric_is_not_listed(self):
        out = self._look_at_a_visited_room(performance={"speed": 9, "capacity": 0})
        self.assertNotIn("Capacity", out)


class TestReadlineSetup(unittest.TestCase):
    """setup_readline is CLI-only and needs a TTY-ish readline, so it is
    exercised against a stand-in. The completer it installs is real logic."""

    def _setup_with_fake_readline(self):
        game = build_real_game()
        fake = unittest.mock.MagicMock()
        captured = {}
        fake.set_completer.side_effect = lambda fn: captured.update(completer=fn)
        with unittest.mock.patch.dict(sys.modules, {"readline": fake}):
            ok = game.setup_readline()
        return ok, captured.get("completer"), fake

    def test_it_reports_success_when_readline_is_available(self):
        ok, _, _ = self._setup_with_fake_readline()
        self.assertTrue(ok)

    def test_it_installs_a_completer(self):
        _, completer, fake = self._setup_with_fake_readline()
        self.assertIsNotNone(completer)
        fake.parse_and_bind.assert_called()

    def test_the_completer_completes_a_command(self):
        _, completer, _ = self._setup_with_fake_readline()
        self.assertEqual(completer("loo", 0), "look")

    def test_the_completer_walks_its_matches_by_state(self):
        _, completer, _ = self._setup_with_fake_readline()
        first, second = completer("s", 0), completer("s", 1)
        self.assertNotEqual(first, second)

    def test_the_completer_returns_none_past_the_last_match(self):
        _, completer, _ = self._setup_with_fake_readline()
        self.assertIsNone(completer("zzzznotacommand", 0))

    def test_a_missing_readline_is_reported_not_raised(self):
        """Readline is absent on some platforms, which must not be fatal."""
        game = build_real_game()
        real_import = builtins.__import__

        def no_readline(name, *args, **kwargs):
            if name == "readline":
                raise ImportError("no readline here")
            return real_import(name, *args, **kwargs)

        with unittest.mock.patch.object(builtins, "__import__", no_readline):
            with unittest.mock.patch("sys.stdout", new=io.StringIO()):
                self.assertFalse(game.setup_readline())


class TestTheReplLoop(unittest.TestCase):
    """`start` is the terminal entry point. The web build never touches it, so
    its quit and interrupt paths were entirely unexercised."""

    def _run(self, inputs, answers=None, game=None, **attrs):
        """Drive start() with a scripted stdin, returning what it printed.

        The stand-in echoes its prompt, because the real `input` writes it to
        stdout and the assertions here read stdout. It also routes by prompt:
        `inputs` answers the main "> " loop and `answers` the yes/no questions,
        since a single queue would let a scripted "y" be eaten by the command
        prompt and never reach the question it was written for. Running out of
        input raises EOFError, which is what a closed stdin does.
        """
        game = game or build_real_game()
        for key, value in attrs.items():
            setattr(game, key, value)
        out = io.StringIO()
        commands = iter(inputs)
        replies = iter(answers or [])

        def fake_input(prompt=""):
            out.write(prompt)
            source = replies if prompt.strip().endswith(("(y/n):", "(y/n)")) else commands
            try:
                return next(source)
            except StopIteration:
                raise EOFError from None

        with unittest.mock.patch.object(builtins, "input", fake_input), \
             unittest.mock.patch.object(game, "setup_readline", lambda: False), \
             unittest.mock.patch("sys.stdout", new=out):
            game.start()
        return game, out.getvalue()

    def test_a_command_is_run_and_its_output_printed(self):
        _, printed = self._run(["look"])
        self.assertIn("LOCATION", printed)

    def test_end_of_input_exits_rather_than_looping(self):
        game, printed = self._run([])
        self.assertTrue(game.game_over)
        self.assertIn("Exiting", printed)

    def test_an_interrupt_with_unsaved_work_offers_to_save(self):
        _, printed = self._run([], changes_since_save=True)
        self.assertIn("Save before exiting?", printed)

    def test_declining_the_save_prompt_still_exits(self):
        game, printed = self._run([], answers=["n"], changes_since_save=True)
        self.assertTrue(game.game_over)
        self.assertIn("Exiting", printed)

    def test_accepting_the_save_prompt_saves(self):
        game = build_real_game()
        game.save_load = unittest.mock.MagicMock()
        game.save_load.save_game.return_value = "Game saved to test.json"
        self._run([], answers=["y"], game=game, changes_since_save=True)
        game.save_load.save_game.assert_called_once()

    def test_a_clean_tree_is_not_asked_about_saving(self):
        _, printed = self._run([], changes_since_save=False)
        self.assertNotIn("Save before exiting?", printed)

    def test_interrupting_the_save_prompt_itself_exits_cleanly(self):
        """Ctrl-C at the question is a 'no', not a crash."""
        game, printed = self._run([], answers=[], changes_since_save=True)
        self.assertTrue(game.game_over)
        self.assertIn("Exiting", printed)

    def test_a_blank_line_is_skipped_without_output(self):
        _, printed = self._run(["", "look"])
        self.assertIn("LOCATION", printed)

    def test_victory_offers_a_replay_and_declining_says_goodbye(self):
        game, printed = self._run(["n"], game_over=True, victory=True)
        self.assertIn("play again", printed.lower())
        self.assertIn("Goodbye", printed)

    def test_losing_exits_without_offering_a_replay(self):
        _, printed = self._run([], game_over=True, victory=False)
        self.assertNotIn("play again", printed.lower())


class TestSmallDelegations(unittest.TestCase):
    def test_the_hint_counter_can_be_set(self):
        """Save/load restores it through this setter."""
        game = build_real_game()
        game.puzzle_hints_used = 2
        self.assertEqual(game.puzzles.hints_used, 2)

    def test_the_memory_minigame_is_gated_on_knowledge(self):
        game = build_real_game()
        game.player.knowledge["memory"] = 0
        self.assertIn("more knowledge", game.start_memory_minigame())

    def test_toggling_a_simulation_that_cannot_toggle_says_so(self):
        game = build_real_game()
        game.player.knowledge["memory"] = 5
        game.start_memory_minigame()
        self.assertIn("doesn't support", game.handle_simulation("toggle", []))


if __name__ == "__main__":
    unittest.main()
