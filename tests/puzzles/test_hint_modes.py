#!/usr/bin/env python3
"""
ABOUTME: Difficulty modes change what a hint costs, never what it reveals.
ABOUTME: Knowledge stays a pure function of solved puzzles in every mode.
"""

import unittest

from computerquest.mechanics.puzzles import HintMode, PuzzleSession, load_registry
from computerquest.models.component import Component
from computerquest.models.player import Player

# A representative shipped puzzle. Tests that care about hint counts read
# them from the registry rather than assuming.
PUZZLE = "l1_lru_basic"


def _session(puzzle_ids=(PUZZLE,), mode=None):
    registry = load_registry()
    room = Component(name="Test Room", description="hint-mode tests")
    room.puzzles = list(puzzle_ids)
    player = Player(location=room, name="Tester")
    session = PuzzleSession(registry, player, {"test_room": room})
    if mode is not None:
        session.hint_mode = mode
    return session, player


def _multi_hint_puzzle(registry):
    for p in registry.by_id.values():
        if len(p.hints) >= 2:
            return p
    return None


class TestModeDefaults(unittest.TestCase):
    def test_standard_is_the_default(self):
        session, _ = _session()
        self.assertEqual(session.hint_mode, HintMode.STANDARD)

    def test_modes_are_named_not_numbered(self):
        self.assertEqual(
            {m.value for m in HintMode}, {"learning", "standard", "strict"}
        )


class TestStandardModeIsUnchanged(unittest.TestCase):
    """Decision 3's bargain must survive exactly as it was for the default."""

    def test_first_hint_is_free(self):
        session, player = _session()
        session.start(PUZZLE)
        self.assertIn("Hint:", session.hint())
        self.assertNotIn(PUZZLE, player.attempted_puzzles)

    def test_second_hint_marks_attempted(self):
        registry = load_registry()
        puzzle = _multi_hint_puzzle(registry)
        if puzzle is None:
            self.skipTest("no shipped puzzle carries two hints")
        session, player = _session((puzzle.id,))
        session.start(puzzle.id)
        session.hint()
        out = session.hint()
        self.assertIn("counts as attempted", out)
        self.assertIn(puzzle.id, player.attempted_puzzles)


class TestLearningMode(unittest.TestCase):
    """Hints flow freely. The point is a new player can lean on them without
    quietly forfeiting the knowledge they are about to earn."""

    def test_hints_never_mark_a_puzzle_attempted(self):
        registry = load_registry()
        puzzle = _multi_hint_puzzle(registry)
        if puzzle is None:
            self.skipTest("no shipped puzzle carries two hints")
        session, player = _session((puzzle.id,), mode=HintMode.LEARNING)
        session.start(puzzle.id)
        session.hint()
        out = session.hint()
        self.assertNotIn(puzzle.id, player.attempted_puzzles)
        self.assertNotIn("counts as attempted", out)

    def test_a_hinted_solve_still_earns_knowledge(self):
        session, player = _session(mode=HintMode.LEARNING)
        session.start(PUZZLE)
        session.hint()
        canonical = session.registry.canonical_answer(PUZZLE)
        session.answer(" ".join(str(c) for c in canonical))
        self.assertIn(PUZZLE, player.solved_puzzles)
        self.assertGreater(player.knowledge["memory"], 0)


class TestStrictMode(unittest.TestCase):
    """Hints are withheld, but the explanation after an answer is not: strict
    means no help before committing, not learning nothing afterwards."""

    def test_hints_are_refused(self):
        session, player = _session(mode=HintMode.STRICT)
        session.start(PUZZLE)
        out = session.hint()
        self.assertNotIn("Hint:", out)
        self.assertIn("strict", out.lower())
        self.assertEqual(session.hints_used, 0)
        self.assertNotIn(PUZZLE, player.attempted_puzzles)

    def test_the_explanation_still_follows_an_answer(self):
        session, _ = _session(mode=HintMode.STRICT)
        session.start(PUZZLE)
        out = session.answer("H H H H H H H")
        self.assertIn("Not quite", out)
        explanation = session.registry.by_id[PUZZLE].explanation.strip()
        self.assertIn(explanation.splitlines()[0][:25], out)


class TestRepeatedHintsAreAcknowledged(unittest.TestCase):
    """Asking again after the list is exhausted should not read like a bug."""

    def test_exhausted_hints_say_so(self):
        session, _ = _session()
        session.start(PUZZLE)
        for _ in range(len(session.registry.by_id[PUZZLE].hints)):
            session.hint()
        self.assertIn("no more", session.hint().lower())


class TestKnowledgeContractHolds(unittest.TestCase):
    """Decision 5: knowledge is a function of solved puzzles in every mode."""

    def test_mode_does_not_move_the_meter_by_itself(self):
        for mode in HintMode:
            with self.subTest(mode=mode):
                session, player = _session(mode=mode)
                session.start(PUZZLE)
                session.hint()
                self.assertEqual(player.knowledge["memory"], 0)


class TestModeSurvivesASave(unittest.TestCase):
    """A difficulty choice the player made must not evaporate on reload."""

    def test_mode_roundtrips(self):
        import json
        import tempfile
        from pathlib import Path

        from tests._helpers import build_real_game

        with tempfile.TemporaryDirectory() as tmp:
            game = build_real_game()
            game.save_load.save_root = Path(tmp)
            game.feed("difficulty strict")
            self.assertEqual(game.puzzles.hint_mode, HintMode.STRICT)
            game.save_load.save_game("m")

            fresh = build_real_game()
            fresh.save_load.save_root = Path(tmp)
            fresh.save_load.load_game("m")
            self.assertEqual(fresh.puzzles.hint_mode, HintMode.STRICT)
            blob = json.loads((Path(tmp) / "m.json").read_text())
            self.assertEqual(blob["puzzle_session"]["hint_mode"], "strict")

    def test_an_unknown_mode_in_a_file_falls_back(self):
        import json
        import tempfile
        from pathlib import Path

        from tests._helpers import build_real_game

        with tempfile.TemporaryDirectory() as tmp:
            game = build_real_game()
            game.save_load.save_root = Path(tmp)
            game.save_load.save_game("m")
            path = Path(tmp) / "m.json"
            data = json.loads(path.read_text())
            data["puzzle_session"]["hint_mode"] = "nonsense"
            path.write_text(json.dumps(data))

            fresh = build_real_game()
            fresh.save_load.save_root = Path(tmp)
            self.assertIn("loaded", fresh.save_load.load_game("m").lower())
            self.assertEqual(fresh.puzzles.hint_mode, HintMode.STANDARD)


class TestDifficultyCommand(unittest.TestCase):
    def setUp(self):
        from tests._helpers import build_real_game

        self.game = build_real_game()

    def test_bare_command_reports_the_current_mode_and_options(self):
        out = self.game.feed("difficulty")
        self.assertIn("standard", out)
        for mode in ("learning", "strict"):
            self.assertIn(mode, out)

    def test_prefix_is_accepted(self):
        self.game.feed("difficulty lear")
        self.assertEqual(self.game.puzzles.hint_mode, HintMode.LEARNING)

    def test_unknown_mode_is_refused_without_changing_anything(self):
        out = self.game.feed("difficulty wibble")
        self.assertIn("Unknown mode", out)
        self.assertEqual(self.game.puzzles.hint_mode, HintMode.STANDARD)

    def test_mode_alias_works(self):
        self.game.feed("mode strict")
        self.assertEqual(self.game.puzzles.hint_mode, HintMode.STRICT)


if __name__ == "__main__":
    unittest.main()
