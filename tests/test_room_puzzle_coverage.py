#!/usr/bin/env python3
"""
ABOUTME: Pins which rooms hold puzzles and which are empty on purpose.
ABOUTME: Issue #5 — empty is a decision here, so it should fail loudly if edited.
"""

import unittest

from computerquest.mechanics.puzzles.registry import VALID_CATEGORIES
from tests._helpers import build_real_game

# Rooms that hold no puzzle by decision, not by omission. Seven are duplicates
# by their own in-game descriptions, so a puzzle here would either repeat the
# room it duplicates or invent an unrelated lesson in an arbitrary place.
# cpu_package is a lobby: its description is a directory of its children, each
# of which is one step away and already teaches.
INTENTIONALLY_EMPTY = frozenset({
    "cpu_package",     # lobby; core1, l3_cache and pch all teach one step away
    "core2",           # "Like Core 1"; its cu/alu/registers hold pipeline puzzles
    "core2_l1",        # duplicate of core1_l1, which holds two cache puzzles
    "l2_cache2",       # "similar to Core 1's L2 cache"
    "ram_dimm2",       # "identical to DIMM 1"
    "ram_dimm3",       # more of the same capacity
    "ram_dimm4",       # completes the configuration; still DIMM 1
    "pcie_x1_2",       # "identical to the first PCIe x1 slot"
})

MAX_PUZZLES_PER_ROOM = 3  # decision 1


class TestRoomCoverageIsDeliberate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = build_real_game()
        cls.rooms = cls.game.game_map.rooms
        cls.empty = {
            key for key, room in cls.rooms.items()
            if not (getattr(room, "puzzles", None) or [])
        }

    def test_the_empty_rooms_are_exactly_the_intended_ones(self):
        """Fails in both directions: padding one of these, or leaving a new
        room empty, is a decision that should be made rather than drift in."""
        self.assertEqual(self.empty, set(INTENTIONALLY_EMPTY))

    def test_every_intentionally_empty_room_exists(self):
        """Guards the list against a room being renamed out from under it,
        which would silently turn the assertion above into a weaker one."""
        missing = INTENTIONALLY_EMPTY - set(self.rooms)
        self.assertEqual(missing, set())

    def test_most_rooms_teach_something(self):
        taught = len(self.rooms) - len(self.empty)
        self.assertGreater(taught, len(self.rooms) // 2)


class TestBindingsAreWellFormed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = build_real_game()
        cls.registry = cls.game.puzzle_registry

    def test_no_room_exceeds_the_cap(self):
        for key, room in self.game.game_map.rooms.items():
            with self.subTest(room=key):
                self.assertLessEqual(
                    len(getattr(room, "puzzles", None) or []), MAX_PUZZLES_PER_ROOM
                )

    def test_no_puzzle_is_bound_to_two_rooms(self):
        """A puzzle in two rooms would be solvable twice for one reward and
        would make the room a player met it in ambiguous."""
        seen: dict[str, str] = {}
        for key, room in self.game.game_map.rooms.items():
            for puzzle_id in getattr(room, "puzzles", None) or []:
                with self.subTest(puzzle=puzzle_id):
                    self.assertNotIn(puzzle_id, seen, f"also bound to {seen.get(puzzle_id)}")
                    seen[puzzle_id] = key

    def test_every_binding_names_a_real_puzzle(self):
        for key, room in self.game.game_map.rooms.items():
            for puzzle_id in getattr(room, "puzzles", None) or []:
                with self.subTest(room=key, puzzle=puzzle_id):
                    self.assertIn(puzzle_id, self.registry.by_id)

    def test_every_puzzle_is_reachable(self):
        bound = {
            puzzle_id
            for room in self.game.game_map.rooms.values()
            for puzzle_id in getattr(room, "puzzles", None) or []
        }
        self.assertEqual(set(self.registry.by_id) - bound, set())

    def test_every_subject_area_has_an_entry_point(self):
        """The gate is deliberately cross-room: solving a difficulty-1 puzzle
        anywhere in a subject unlocks the difficulty-2 puzzles elsewhere in it.
        So the invariant is per area, not per room, and most rooms legitimately
        hold only gated puzzles. What would strand a player is an area with no
        difficulty-1 puzzle at all, because nothing in it could ever open."""
        entry_points: dict[str, int] = {}
        for puzzle in self.registry.by_id.values():
            if puzzle.difficulty == 1:
                entry_points[puzzle.subject_area] = (
                    entry_points.get(puzzle.subject_area, 0) + 1
                )
        for area in sorted(VALID_CATEGORIES):
            with self.subTest(area=area):
                self.assertGreater(
                    entry_points.get(area, 0), 0,
                    f"{area} has no difficulty-1 puzzle, so nothing in it unlocks",
                )


class TestEveryPuzzleCanActuallyBeUnlocked(unittest.TestCase):
    """Being bound to a room is not the same as being obtainable.

    The gate opens a difficulty-N puzzle only once the player has solved one at
    N-1 or better in the same subject, so a difficulty-3 puzzle in an area with
    no difficulty-2 is bound, validated, reachable by walking, and locked
    forever. Nothing else here would catch that: the binding tests only ask
    whether a room names it.
    """

    def _solve_everything_the_gate_offers(self):
        """Play greedily: sweep every room solving whatever is on offer, and
        repeat until a full pass finds nothing new."""
        game = build_real_game()
        solved: set[str] = set()
        for _ in range(len(game.puzzle_registry.by_id) + 1):
            progress = False
            for room in game.game_map.rooms.values():
                game.player.location = room
                for puzzle in game._gated_room_puzzles():
                    game.player.solved_puzzles.add(puzzle.id)
                    solved.add(puzzle.id)
                    progress = True
                game._recompute_knowledge()
            if not progress:
                break
        return game, solved

    def test_every_shipped_puzzle_can_be_reached_through_the_gate(self):
        game, solved = self._solve_everything_the_gate_offers()
        stranded = set(game.puzzle_registry.by_id) - solved
        self.assertEqual(stranded, set(), f"locked forever: {sorted(stranded)}")

    def test_a_full_run_maxes_every_knowledge_meter(self):
        game, _ = self._solve_everything_the_gate_offers()
        self.assertEqual(
            {area: 5 for area in VALID_CATEGORIES}, dict(game.player.knowledge)
        )


class TestSubjectBalance(unittest.TestCase):
    """Every area should be teachable to its cap, and none should rest on a
    single simulator: storage did, and one of its five puzzles ended up in the
    SSD room asking how far a head travelled."""

    @classmethod
    def setUpClass(cls):
        cls.registry = build_real_game().puzzle_registry

    def test_every_area_has_puzzles(self):
        areas = {p.subject_area for p in self.registry.by_id.values()}
        self.assertEqual(areas, set(VALID_CATEGORIES))

    def test_no_area_rests_on_a_single_simulator(self):
        by_area: dict[str, set[str]] = {}
        for puzzle in self.registry.by_id.values():
            by_area.setdefault(puzzle.subject_area, set()).add(puzzle.simulator)
        for area, simulators in sorted(by_area.items()):
            with self.subTest(area=area):
                self.assertGreater(
                    len(simulators), 1,
                    f"{area} teaches one lesson in {len(simulators)} costume(s)",
                )

    def test_every_area_can_still_reach_the_cap(self):
        totals: dict[str, float] = {}
        for puzzle in self.registry.by_id.values():
            totals[puzzle.subject_area] = (
                totals.get(puzzle.subject_area, 0.0) + puzzle.knowledge_weight()
            )
        for area, weight in sorted(totals.items()):
            with self.subTest(area=area):
                self.assertGreaterEqual(weight, 5.0)


if __name__ == "__main__":
    unittest.main()
