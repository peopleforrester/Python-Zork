#!/usr/bin/env python3
"""
ABOUTME: Adaptive difficulty: a room with several puzzles offers the one that
ABOUTME: matches the player's demonstrated standing in that subject area.
"""

import unittest

from computerquest.mechanics.puzzles import PuzzleSession, load_registry
from computerquest.models.component import Component
from computerquest.models.player import Player

# core1_l1 ships difficulty 1 then 2; bios ships difficulty 1 then 3.
EASY, HARD = "l1_lru_basic", "l1_associativity_2way"


def _session(puzzle_ids=(EASY, HARD)):
    registry = load_registry()
    room = Component(name="Test Room", description="adaptive-difficulty tests")
    room.puzzles = list(puzzle_ids)
    player = Player(location=room, name="Tester")
    return PuzzleSession(registry, player, {"test_room": room}), player


def _solve(player, registry, area, count, difficulty=1):
    """Mark `count` puzzles in `area` solved, without touching the room."""
    picked = [p for p in registry.by_id.values()
              if p.subject_area == area and p.difficulty == difficulty][:count]
    for p in picked:
        player.solved_puzzles.add(p.id)
        player.attempted_puzzles.add(p.id)
    return picked


def _struggle(player, registry, area, count, exclude=()):
    """Mark `count` puzzles in `area` attempted but never solved."""
    picked = [p for p in registry.by_id.values()
              if p.subject_area == area and p.id not in player.solved_puzzles
              and p.id not in exclude][:count]
    for p in picked:
        player.attempted_puzzles.add(p.id)
    return picked


def _unlock(player, registry, area, room_ids, count=1):
    """Solve `count` puzzles in `area` from outside `room_ids`.

    The gate needs a solved puzzle of difficulty >= N-1 in the area, so this is
    what makes a room's higher-difficulty puzzle visible alongside its easier
    one. Without it the gate, not the ordering, decides what a room shows.
    """
    picked = [p for p in registry.by_id.values()
              if p.subject_area == area and p.id not in room_ids][:count]
    for p in picked:
        player.solved_puzzles.add(p.id)
        player.attempted_puzzles.add(p.id)
    return picked


class TestStandingSignal(unittest.TestCase):
    """Standing is derived from solved vs attempted-but-unsolved, per area."""

    def setUp(self):
        self.session, self.player = _session()
        self.reg = self.session.registry

    def test_fresh_player_is_neutral(self):
        self.assertEqual(self.session.area_standing("memory"), "neutral")

    def test_unsolved_attempts_mark_struggling(self):
        _struggle(self.player, self.reg, "memory", 2)
        self.assertEqual(self.session.area_standing("memory"), "struggling")

    def test_clean_solves_mark_strong(self):
        _solve(self.player, self.reg, "cpu", 2)
        self.assertEqual(self.session.area_standing("cpu"), "strong")

    def test_a_single_stumble_does_not_erase_a_strong_record(self):
        _solve(self.player, self.reg, "cpu", 2)
        _struggle(self.player, self.reg, "cpu", 1)
        self.assertNotEqual(self.session.area_standing("cpu"), "strong")

    def test_standing_is_per_area_not_global(self):
        _struggle(self.player, self.reg, "memory", 2)
        self.assertEqual(self.session.area_standing("memory"), "struggling")
        self.assertEqual(self.session.area_standing("storage"), "neutral")


class TestAdaptiveOrdering(unittest.TestCase):
    """The room's offer order follows standing; ties keep the authored order."""

    def test_neutral_player_sees_the_authored_order(self):
        session, player = _session()
        _unlock(player, session.registry, "memory", (EASY, HARD))
        self.assertEqual([p.id for p in session.gated_room_puzzles()], [EASY, HARD])

    def test_struggling_player_is_offered_the_easiest_first(self):
        session, player = _session()
        _unlock(player, session.registry, "memory", (EASY, HARD))
        _struggle(player, session.registry, "memory", 2, exclude=(EASY, HARD))
        self.assertEqual(session.area_standing("memory"), "struggling")
        order = [p.id for p in session.gated_room_puzzles()]
        self.assertEqual(order, [EASY, HARD])

    def test_strong_player_is_offered_the_hardest_first(self):
        session, player = _session()
        # Solve memory puzzles elsewhere so the room's two stay unsolved.
        for p in session.registry.by_id.values():
            if p.subject_area == "memory" and p.id not in (EASY, HARD):
                player.solved_puzzles.add(p.id)
                player.attempted_puzzles.add(p.id)
        order = [p.id for p in session.gated_room_puzzles()]
        self.assertEqual(order[0], HARD)

    def test_ordering_never_adds_or_drops_puzzles(self):
        session, player = _session()
        _unlock(player, session.registry, "memory", (EASY, HARD))
        _struggle(player, session.registry, "memory", 2, exclude=(EASY, HARD))
        self.assertEqual(sorted(p.id for p in session.gated_room_puzzles()), sorted([EASY, HARD]))

    def test_equal_difficulty_keeps_authored_order(self):
        """kernel ships two difficulty-2 puzzles; a tie must be stable."""
        pair = ("signature_near_miss", "signature_rootkit_hunt")
        session, player = _session(pair)
        _unlock(player, session.registry, "security", pair)
        _struggle(player, session.registry, "security", 2, exclude=pair)
        self.assertEqual([p.id for p in session.gated_room_puzzles()], list(pair))


class TestAdaptationReachesThePlayer(unittest.TestCase):
    """Ordering is only meaningful if the presented puzzle follows it."""

    def test_auto_prompt_offers_the_adapted_puzzle(self):
        session, player = _session()
        for p in session.registry.by_id.values():
            if p.subject_area == "memory" and p.id not in (EASY, HARD):
                player.solved_puzzles.add(p.id)
                player.attempted_puzzles.add(p.id)
        out = session.maybe_auto_prompt()
        self.assertIn(session.registry.by_id[HARD].title, out)

    def test_listing_shows_the_adapted_order(self):
        session, player = _session()
        _unlock(player, session.registry, "memory", (EASY, HARD))
        _struggle(player, session.registry, "memory", 2, exclude=(EASY, HARD))
        listing = session.list_room_puzzles()
        self.assertLess(listing.index(EASY), listing.index(HARD))

    def test_gate_rules_are_unchanged_by_adaptation(self):
        """A difficulty-3 puzzle still needs its prerequisite, however strong
        the player looks. Adaptation reorders; it does not unlock."""
        session, player = _session(("signature_first_match",))  # difficulty 3
        self.assertEqual(session.gated_room_puzzles(), [])

    def test_knowledge_is_untouched_by_adaptation(self):
        session, player = _session()
        _struggle(player, session.registry, "memory", 2)
        session.gated_room_puzzles()
        self.assertEqual(player.knowledge["memory"], 0)


if __name__ == "__main__":
    unittest.main()
