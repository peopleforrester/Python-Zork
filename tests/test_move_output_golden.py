#!/usr/bin/env python3
"""
ABOUTME: Pins move()'s rendered output byte-for-byte across every room and exit.
ABOUTME: Captured before move() stopped duplicating player.look()'s readout.
"""

import json
import pathlib
import unittest

from tests._helpers import build_real_game

_GOLDEN = pathlib.Path(__file__).parent / "fixtures" / "golden_move_output.json"


def _capture() -> dict[str, str]:
    """Every room, every exit, in both the fresh and the visited state.

    The visited pass sets security level, data types and performance so the
    technical readout is exercised rather than skipped, which is the block the
    duplication lived in.
    """
    captured: dict[str, str] = {}
    for visited in (False, True):
        game = build_real_game()
        if visited:
            for room in game.game_map.rooms.values():
                room.mark_visited()
                room.security_level = 3
                room.data_types = ["instructions", "operands"]
                room.performance = {"speed": 9, "capacity": 0}
        for key, room in sorted(game.game_map.rooms.items()):
            for direction in sorted(room.doors):
                game.player.location = room
                # Auto-prompt is stateful across moves and is covered
                # elsewhere; suppressing it keeps this about the rendering.
                game.puzzles.prompted_rooms = set(game.game_map.rooms)
                captured[f"{'v' if visited else 'f'}|{key}|{direction}"] = game.move(direction)
    return captured


class TestMoveOutputUnchanged(unittest.TestCase):
    """move() rendered its own copy of the technical readout that
    player.look() already built, so the two could drift and show different
    details for the same room. This pins the output across that collapse."""

    @classmethod
    def setUpClass(cls):
        cls.golden = json.loads(_GOLDEN.read_text())
        cls.actual = _capture()

    def test_every_room_and_exit_is_covered(self):
        self.assertEqual(sorted(self.actual), sorted(self.golden))

    def test_output_is_byte_identical(self):
        for key in sorted(self.golden):
            with self.subTest(case=key):
                self.assertEqual(self.actual[key], self.golden[key])

    def test_the_visited_pass_actually_renders_the_readout(self):
        """Guards the fixture itself: if the technical block stopped being
        emitted, the golden would still match a golden that never had it."""
        visited = [v for k, v in self.actual.items() if k.startswith("v|")]
        self.assertTrue(visited)
        self.assertTrue(any("Security Level: 3" in v for v in visited))
        self.assertTrue(any("Performance Metrics:" in v for v in visited))

    def test_the_fresh_pass_omits_the_readout(self):
        fresh = [v for k, v in self.actual.items() if k.startswith("f|")]
        self.assertFalse(any("Security Level:" in v for v in fresh))


if __name__ == "__main__":
    unittest.main()
