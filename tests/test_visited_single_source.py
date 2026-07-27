#!/usr/bin/env python3
"""
ABOUTME: Pins "visited" to one source of truth, Component.visited.
ABOUTME: The ASCII map and the web snapshot disagreed about the starting room.
"""

import unittest

from tests._helpers import build_real_game


class TestVisitedHasOneSource(unittest.TestCase):
    """map_grid used to be a parallel copy of Component.visited, hand-synced in
    four places. The starting room was marked in map_grid but not on the
    Component, so the ASCII map and the React map disagreed at turn 0."""

    def setUp(self) -> None:
        self.game = build_real_game()

    def test_starting_room_is_visited_on_the_component(self):
        self.assertTrue(self.game.player.location.visited)

    def test_ascii_map_and_snapshot_agree_at_turn_zero(self):
        start_id = self.game._current_room_id()
        snap = next(r for r in self.game.snapshot()["rooms"] if r["id"] == start_id)
        self.assertEqual(snap["visited"], self.game.map_grid[start_id]["visited"])
        self.assertTrue(snap["visited"])

    def test_map_grid_is_derived_from_rooms(self):
        """Every room appears, and each entry mirrors the component's flag."""
        self.assertEqual(set(self.game.map_grid), set(self.game.game_map.rooms))
        for room_id, room in self.game.game_map.rooms.items():
            self.assertEqual(self.game.map_grid[room_id]["visited"], room.visited)

    def test_moving_updates_both_views_together(self):
        before = sum(1 for v in self.game.map_grid.values() if v["visited"])
        self.game.feed("n")
        after_grid = sum(1 for v in self.game.map_grid.values() if v["visited"])
        after_rooms = sum(1 for r in self.game.game_map.rooms.values() if r.visited)
        self.assertGreater(after_grid, before)
        self.assertEqual(after_grid, after_rooms)

    def test_marking_a_component_visited_shows_up_in_map_grid(self):
        """No hand-sync step: writing the component is enough."""
        target_id, target = next(
            (rid, r) for rid, r in self.game.game_map.rooms.items() if not r.visited
        )
        self.assertFalse(self.game.map_grid[target_id]["visited"])
        target.mark_visited()
        self.assertTrue(self.game.map_grid[target_id]["visited"])


if __name__ == "__main__":
    unittest.main()
