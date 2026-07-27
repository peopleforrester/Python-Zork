#!/usr/bin/env python3
"""
ABOUTME: End-to-end playthrough driving a real Game to victory via feed().
ABOUTME: Guards the win condition, which older victory tests only mocked.
"""

import unittest
from collections import deque

from computerquest.config import VIRUS_TYPES, is_virus_name
from tests._helpers import build_real_game


def _route(rooms, start, goal):
    """Shortest door path from `start` to `goal` as a list of directions.

    Computed rather than hardcoded so the test survives map edits and doubles
    as a reachability check on the door graph.
    """
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        current, path = queue.popleft()
        if current == goal:
            return path
        for direction, dest in rooms[current].doors.items():
            key = dest.key
            if key and key not in seen:
                seen.add(key)
                queue.append((key, path + [direction]))
    return None


class TestPlaythroughToVictory(unittest.TestCase):
    """Walk the real world, scan, quarantine all five viruses, and win.

    This exercises the paths the unit tests mock out: movement through the
    door graph, Player.scan, Player.quarantine (whose room and inventory
    branches share one body), the derived Game.all_viruses_found, and the
    victory flip inside QuarantineCommand.
    """

    def setUp(self) -> None:
        self.game = build_real_game()
        self.rooms = self.game.game_map.rooms
        self.virus_rooms = {
            room_id: next(i for i in room.items if is_virus_name(i))
            for room_id, room in self.rooms.items()
            if any(is_virus_name(i) for i in room.items)
        }

    def test_every_virus_room_is_reachable(self):
        """A virus behind an unreachable door would make the game unwinnable."""
        start = self.game._current_room_id()
        for room_id in self.virus_rooms:
            self.assertIsNotNone(
                _route(self.rooms, start, room_id),
                f"no path from {start} to {room_id}",
            )

    def test_all_five_virus_types_are_placed_in_the_world(self):
        self.assertEqual(sorted(self.virus_rooms.values()), sorted(VIRUS_TYPES))

    def test_full_playthrough_reaches_victory(self):
        game = self.game
        self.assertFalse(game.victory)
        self.assertFalse(game.all_viruses_found)

        for room_id, virus in self.virus_rooms.items():
            for direction in _route(self.rooms, game._current_room_id(), room_id):
                game.feed(direction)
            self.assertEqual(game._current_room_id(), room_id)

            game.feed("scan")
            self.assertIn(virus, game.player.found_viruses)

            result = game.feed(f"quarantine {virus}")
            self.assertIn("quarantined", result.lower())
            self.assertIn(virus, game.player.quarantined_viruses)

        self.assertEqual(len(game.player.found_viruses), len(VIRUS_TYPES))
        self.assertEqual(len(game.player.quarantined_viruses), len(VIRUS_TYPES))
        self.assertTrue(game.all_viruses_found)
        self.assertTrue(game.victory)
        self.assertTrue(game.game_over)

    def test_snapshot_reports_the_win_to_the_frontend(self):
        """The web client learns about victory only through the snapshot."""
        game = self.game
        for room_id, virus in self.virus_rooms.items():
            for direction in _route(self.rooms, game._current_room_id(), room_id):
                game.feed(direction)
            game.feed("scan")
            game.feed(f"quarantine {virus}")

        snapshot = game.snapshot()
        self.assertTrue(snapshot["victory"])
        self.assertTrue(snapshot["game_over"])
        self.assertTrue(snapshot["all_viruses_found"])
        self.assertEqual(len(snapshot["quarantined_viruses"]), len(VIRUS_TYPES))
        # Rooms walked through are reported visited, from the single source.
        self.assertGreater(sum(1 for r in snapshot["rooms"] if r["visited"]), 1)


if __name__ == "__main__":
    unittest.main()
