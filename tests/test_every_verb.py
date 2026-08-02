#!/usr/bin/env python3
"""
ABOUTME: Runs every registered verb so none can rot unnoticed.
ABOUTME: Six were reachable by players and exercised by no test at all.
"""

import unittest

from tests._helpers import build_real_game

# QuitCommand and its aliases call input() in the CLI build, which would block
# a test run forever. server.py intercepts them before Game.feed for the same
# reason; test_server covers that path.
BLOCKING = frozenset({"quit", "exit", "q"})

NOT_RECOGNIZED = "not recognized"


class TestEveryVerbResponds(unittest.TestCase):
    """A verb that no test ever runs is where the last few defects hid: 33
    commands answered 'No help for X' while a test asserted only that the
    output was non-empty. This runs the whole surface."""

    @classmethod
    def setUpClass(cls):
        cls.verbs = sorted(set(build_real_game().command_processor.commands) - BLOCKING)

    def test_the_registry_is_not_trivially_small(self):
        """Guards the sweep itself: if the command table stopped resolving,
        every assertion below would pass over an empty list."""
        self.assertGreater(len(self.verbs), 60)

    def test_no_bare_verb_crashes(self):
        for verb in self.verbs:
            game = build_real_game()
            with self.subTest(verb=verb):
                try:
                    game.feed(verb)
                except Exception as exc:  # noqa: BLE001 — any crash is the defect
                    self.fail(f"{verb!r} raised {type(exc).__name__}: {exc}")

    def test_every_verb_is_dispatched(self):
        """'not recognized' from a registered verb means the table and the
        resolver disagree."""
        for verb in self.verbs:
            game = build_real_game()
            with self.subTest(verb=verb):
                self.assertNotIn(NOT_RECOGNIZED, game.feed(verb).lower())

    def test_no_bare_verb_answers_with_nothing(self):
        """Silence reads as a hung game. A verb needing an argument should say
        so, which is what `read` does with 'What do you want to read?'."""
        for verb in self.verbs:
            game = build_real_game()
            with self.subTest(verb=verb):
                self.assertTrue(game.feed(verb).strip(), f"{verb!r} returned nothing")

    def test_an_unregistered_verb_is_still_rejected(self):
        """The inverse, so the three assertions above cannot pass by the
        resolver having become permissive."""
        self.assertIn(NOT_RECOGNIZED, build_real_game().feed("zzzznotaverb").lower())


class TestVerbsSurviveAnArgument(unittest.TestCase):
    """Bare verbs exercise the no-argument branch only, and several commands
    do their real work in the other one."""

    def test_no_verb_crashes_on_a_nonsense_argument(self):
        game_verbs = sorted(set(build_real_game().command_processor.commands) - BLOCKING)
        for verb in game_verbs:
            game = build_real_game()
            with self.subTest(verb=verb):
                try:
                    game.feed(f"{verb} zzzznonsense")
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"{verb!r} raised {type(exc).__name__} on an argument: {exc}")


if __name__ == "__main__":
    unittest.main()
