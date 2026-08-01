#!/usr/bin/env python3
"""
ABOUTME: `objectives` shows the next few steps, derived from live state.
ABOUTME: It narrows the search without naming the room a virus is hiding in.
"""

import unittest

from computerquest.config import VIRUS_TYPES, is_virus_name
from tests._helpers import build_real_game


class TestObjectivesCommand(unittest.TestCase):
    def setUp(self):
        self.game = build_real_game()

    def test_command_exists_and_returns_text(self):
        out = self.game.feed("objectives")
        self.assertTrue(out.strip())

    def test_it_is_read_only(self):
        """Asking what to do next is not an action."""
        before = self.game.turns
        self.game.feed("objectives")
        self.assertEqual(self.game.turns, before)

    def test_it_does_not_dirty_the_save_flag(self):
        self.game.changes_since_save = False
        self.game.feed("objectives")
        self.assertFalse(self.game.changes_since_save)

    def test_it_does_not_disturb_an_active_puzzle(self):
        self.game.feed("n")
        active = self.game.current_puzzle
        self.game.feed("objectives")
        self.assertIs(self.game.current_puzzle, active)


class TestProgressiveReveal(unittest.TestCase):
    """A full dump is the failure mode being avoided; so is an empty screen."""

    def setUp(self):
        self.game = build_real_game()

    def test_only_a_few_objectives_are_shown(self):
        lines = [
            line for line in self.game.feed("objectives").splitlines()
            if line.strip().startswith(("-", "•", "*"))
        ]
        self.assertGreater(len(lines), 0)
        self.assertLessEqual(len(lines), 6)

    def test_it_reflects_progress_rather_than_repeating(self):
        first = self.game.feed("objectives")
        # Quarantine everything; the objectives must not read the same after.
        for room in self.game.game_map.rooms.values():
            for item in list(room.items):
                if is_virus_name(item):
                    self.game.player.found_viruses.append(item)
                    self.game.player.quarantined_viruses.append(item)
        self.assertNotEqual(first, self.game.feed("objectives"))

    def test_a_finished_game_says_so_rather_than_listing_nothing(self):
        for room in self.game.game_map.rooms.values():
            room.mark_visited()
        for virus in VIRUS_TYPES:
            self.game.player.found_viruses.append(virus)
            self.game.player.quarantined_viruses.append(virus)
        for pid in self.game.puzzle_registry.by_id:
            self.game.player.solved_puzzles.add(pid)
        self.game._recompute_knowledge()
        out = self.game.feed("objectives")
        self.assertTrue(out.strip())
        self.assertNotIn("- ", out.split("\n")[-1])


class TestItDoesNotSpoilTheSearch(unittest.TestCase):
    """Finding a virus is the investigation. Objectives narrow the space; they
    do not hand over the answer."""

    def setUp(self):
        self.game = build_real_game()

    def test_no_unfound_virus_room_is_named(self):
        virus_rooms = {
            rid for rid, room in self.game.game_map.rooms.items()
            if any(is_virus_name(i) for i in room.items)
        }
        out = self.game.feed("objectives").lower()
        for room_id in virus_rooms:
            name = self.game.game_map.rooms[room_id].name.lower()
            with self.subTest(room=room_id):
                self.assertNotIn(name, out)

    def test_a_found_virus_may_be_named(self):
        """Once located, telling the player where to go is help, not a spoiler."""
        room_id, room = next(
            (rid, r) for rid, r in self.game.game_map.rooms.items()
            if any(is_virus_name(i) for i in r.items)
        )
        virus = next(i for i in room.items if is_virus_name(i))
        self.game.player.found_viruses.append(virus)
        self.assertIn(virus, self.game.feed("objectives"))


class TestDerivedFromLiveState(unittest.TestCase):
    """Hand-maintained lists drift from content the way the puzzle answer
    comments did. Everything here must come from the world."""

    def setUp(self):
        self.game = build_real_game()

    def test_puzzle_progress_is_reflected(self):
        before = self.game.feed("objectives")
        for pid in list(self.game.puzzle_registry.by_id)[:10]:
            self.game.player.solved_puzzles.add(pid)
        self.game._recompute_knowledge()
        self.assertNotEqual(before, self.game.feed("objectives"))

    def test_exploration_progress_is_reflected(self):
        before = self.game.feed("objectives")
        for room in self.game.game_map.rooms.values():
            room.mark_visited()
        self.assertNotEqual(before, self.game.feed("objectives"))

    def test_counts_match_the_world(self):
        """Totals must be computed, not typed into a string."""
        out = self.game.feed("objectives")
        self.assertIn(str(len(VIRUS_TYPES)), out)


class TestRendering(unittest.TestCase):
    """A fixed-width box cannot align around variable-length content, so this
    panel uses rules. Long lines wrap rather than running off a narrow view."""

    def setUp(self):
        self.game = build_real_game()

    def test_rules_are_equal_length(self):
        lines = self.game.feed("objectives").splitlines()
        self.assertEqual(len(lines[0]), len(lines[-1]))

    def test_no_line_exceeds_the_panel_width(self):
        for line in self.game.feed("objectives").splitlines():
            self.assertLessEqual(len(line), 70)

    def test_the_counts_do_not_contradict_each_other(self):
        """Reporting viruses 'still loose' while telling the player to
        quarantine one they already found read as a bug."""
        for m in ("s", "s", "w", "w"):
            self.game.feed(m)
        self.game.feed("scan")
        out = self.game.feed("objectives")
        if "Quarantine" in out:
            self.assertNotIn(f"{len(VIRUS_TYPES)} of {len(VIRUS_TYPES)} viruses", out)


if __name__ == "__main__":
    unittest.main()
