#!/usr/bin/env python3
"""
ABOUTME: Guards the ASCII map's room-position table against gaps and overlaps.
ABOUTME: A room with no position silently never renders, even when visited.
"""

import os
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

from computerquest.utils.map_renderer import MAP_POSITIONS, render_map
from tests._helpers import build_real_game

_SOURCE = Path(__file__).parent.parent / "computerquest" / "utils" / "map_renderer.py"


def _positions() -> dict[str, tuple[int, int]]:
    """The canonical placement table.

    This used to regex the literal out of render_map's source, because the
    table was a local inside that function and there was no other way to reach
    it. It is now a module constant, shared with the web map's snapshot, so the
    test reads the real object instead of parsing text that formatting could
    silently break.
    """
    return dict(MAP_POSITIONS)


class TestMapPositionTable(unittest.TestCase):
    def setUp(self) -> None:
        self.game = build_real_game()
        self.positions = _positions()

    def test_every_room_has_a_map_position(self):
        """A room missing here renders no marker however often it is visited."""
        missing = sorted(set(self.game.game_map.rooms) - set(self.positions))
        self.assertEqual(missing, [], f"rooms with no map position: {missing}")

    def test_no_position_refers_to_a_room_that_does_not_exist(self):
        stale = sorted(set(self.positions) - set(self.game.game_map.rooms))
        self.assertEqual(stale, [], f"positions for unknown rooms: {stale}")

    def test_no_two_rooms_share_a_cell(self):
        """Colliding cells mean one marker silently overwrites the other."""
        collisions = {
            cell: count for cell, count in Counter(self.positions.values()).items() if count > 1
        }
        self.assertEqual(collisions, {}, f"colliding map cells: {collisions}")

    def test_every_position_lands_inside_the_rendered_frame(self):
        """A position past the frame is clipped and never drawn (see pcie_x1_2)."""
        frame = [
            line for line in render_map(self.game, self.game.map_grid).split("\n")
            if line.startswith("|") or line.startswith("+")
        ]
        for name, (row, col) in sorted(self.positions.items()):
            with self.subTest(room=name):
                self.assertLess(row, len(frame), f"{name} row {row} past frame")
                self.assertLess(col, len(frame[row]), f"{name} col {col} past line")

    def test_render_is_deterministic_across_hash_seeds(self):
        """The map merges overlapping component art, so the merge order decides
        which cells win. Driving that from a set made the rendered map depend
        on Python's per-process string hash seed: the same game rendered
        differently between runs. Fresh subprocesses with distinct seeds must
        now agree.
        """
        script = (
            "from tests._helpers import build_real_game;"
            "g=build_real_game();"
            "[r.mark_visited() for r in g.game_map.rooms.values()];"
            "import hashlib;"
            "print(hashlib.sha256(g.display_map().encode()).hexdigest())"
        )
        digests = set()
        for seed in ("0", "1", "42", "12345"):
            env = {**os.environ, "PYTHONHASHSEED": seed}
            out = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True, text=True, env=env,
                cwd=str(Path(__file__).parent.parent), check=True,
            )
            digests.add(out.stdout.strip())
        self.assertEqual(len(digests), 1, f"map render varies by hash seed: {digests}")

    def test_all_visited_rooms_render_a_marker(self):
        """With every room visited, marker count must equal the room count."""
        for room in self.game.game_map.rooms.values():
            room.mark_visited()
        frame = "\n".join(
            line for line in render_map(self.game, self.game.map_grid).split("\n")
            if line.startswith("|") or line.startswith("+")
        )
        markers = frame.count("•") + frame.count("★")
        self.assertEqual(markers, len(self.game.game_map.rooms))

class TestSnapshotShipsGridPositions(unittest.TestCase):
    """The web map draws from these. It used to invent an alphabetical circle
    of its own, which placed unrelated rooms adjacent and drew every corridor
    as a chord across the middle."""

    @classmethod
    def setUpClass(cls):
        from tests._helpers import build_real_game
        cls.snapshot = build_real_game().snapshot()

    def test_every_room_ships_a_grid_position(self):
        for room in self.snapshot["rooms"]:
            with self.subTest(room=room["id"]):
                self.assertIn("grid", room)
                self.assertIn("row", room["grid"])
                self.assertIn("col", room["grid"])

    def test_the_shipped_positions_match_the_ascii_map(self):
        """One source of truth, so the two maps cannot drift apart."""
        from computerquest.utils.map_renderer import MAP_POSITIONS
        for room in self.snapshot["rooms"]:
            with self.subTest(room=room["id"]):
                row, col = MAP_POSITIONS[room["id"]]
                self.assertEqual((room["grid"]["row"], room["grid"]["col"]), (row, col))

    def test_no_two_rooms_ship_the_same_cell(self):
        cells = [(r["grid"]["row"], r["grid"]["col"]) for r in self.snapshot["rooms"]]
        self.assertEqual(len(cells), len(set(cells)))

if __name__ == "__main__":
    unittest.main()
