#!/usr/bin/env python3
"""
ABOUTME: Tests PuzzleSession directly, without constructing a whole Game.
ABOUTME: The extraction's payoff: puzzle flow is unit-testable in isolation.
"""

import unittest

from computerquest.mechanics.puzzles import PuzzleSession, load_registry
from computerquest.models.component import Component
from computerquest.models.player import Player


def _build_session(puzzle_ids):
    """A session over a single synthetic room bound to `puzzle_ids`."""
    registry = load_registry()
    room = Component(name="Test Room", description="a room for session tests")
    room.puzzles = list(puzzle_ids)
    player = Player(location=room, name="Tester")
    session = PuzzleSession(registry, player, {"test_room": room})
    return session, player


class TestSessionStandsAlone(unittest.TestCase):
    """No Game, no world graph, no command processor."""

    def test_current_room_id_resolves_from_the_rooms_map(self):
        session, _ = _build_session(["l1_lru_basic"])
        self.assertEqual(session.current_room_id(), "test_room")

    def test_start_presents_the_only_puzzle(self):
        session, _ = _build_session(["l1_lru_basic"])
        out = session.start()
        self.assertIn("PUZZLE:", out)
        self.assertIsNotNone(session.current)
        self.assertEqual(session.current.id, "l1_lru_basic")

    def test_correct_answer_solves_and_raises_knowledge(self):
        session, player = _build_session(["l1_lru_basic"])
        session.start()
        canonical = session.registry.canonical_answer("l1_lru_basic")
        verdict = session.answer(" ".join(str(c) for c in canonical))
        self.assertIn("Correct!", verdict)
        self.assertIn("l1_lru_basic", player.solved_puzzles)
        self.assertGreater(player.knowledge["memory"], 0)
        self.assertIsNone(session.current)  # ends on commit

    def test_wrong_answer_records_attempt_but_not_solve(self):
        session, player = _build_session(["l1_lru_basic"])
        session.start()
        verdict = session.answer("H H H H H H H")
        self.assertIn("Not quite", verdict)
        self.assertIn("l1_lru_basic", player.attempted_puzzles)
        self.assertNotIn("l1_lru_basic", player.solved_puzzles)

    def test_second_hint_marks_the_puzzle_attempted(self):
        session, player = _build_session(["l1_lru_basic"])
        session.start()
        session.hint()
        self.assertNotIn("l1_lru_basic", player.attempted_puzzles)
        out = session.hint()
        self.assertIn("counts as attempted", out)
        self.assertIn("l1_lru_basic", player.attempted_puzzles)

    def test_skip_clears_the_active_puzzle(self):
        session, _ = _build_session(["l1_lru_basic"])
        session.start()
        self.assertIn("Putting", session.skip())
        self.assertIsNone(session.current)

    def test_auto_prompt_fires_once_per_room(self):
        session, _ = _build_session(["l1_lru_basic"])
        first = session.maybe_auto_prompt()
        self.assertIn("PUZZLE:", first)
        session.skip()
        self.assertEqual(session.maybe_auto_prompt(), "")

    def test_unknown_binding_is_ignored_by_the_gate(self):
        session, _ = _build_session(["no_such_puzzle"])
        self.assertEqual(session.gated_room_puzzles(), [])

    def test_recompute_is_the_single_writer_of_knowledge(self):
        session, player = _build_session(["l1_lru_basic"])
        # A stray direct write is discarded on the next recompute, which is
        # what makes knowledge a pure function of solved puzzles.
        player.knowledge["memory"] = 4
        session.recompute_knowledge()
        self.assertEqual(player.knowledge["memory"], 0)


if __name__ == "__main__":
    unittest.main()
