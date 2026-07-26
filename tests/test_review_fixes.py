#!/usr/bin/env python3
"""
ABOUTME: Regression tests for the code-review fixes (bugs B1-B8, 2026-07).
ABOUTME: Each test pins a specific defect the review found so it can't return.
"""

import unittest

import server
from computerquest.config import VIRUS_TYPES
from computerquest.mechanics.puzzles import load_registry
from computerquest.utils.map_renderer import render_map
from tests._helpers import build_real_game


class TestQuitPrefixInterception(unittest.TestCase):
    """B1: the web server must intercept abbreviated exit verbs before feed()
    reaches QuitCommand, which blocks on input()."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.game = build_real_game()

    def test_full_exit_verbs_resolve_to_themselves(self) -> None:
        for verb in ("quit", "exit", "q"):
            self.assertEqual(server._resolve_verb(self.game, verb), verb)

    def test_abbreviated_exit_verbs_resolve_to_intercepted_form(self) -> None:
        self.assertEqual(server._resolve_verb(self.game, "qui"), "quit")
        self.assertEqual(server._resolve_verb(self.game, "exi"), "exit")

    def test_resolved_abbreviations_are_intercepted(self) -> None:
        for typed in ("qui", "exi", "quit", "exit", "q"):
            self.assertIn(server._resolve_verb(self.game, typed), server._INTERCEPTED_VERBS)

    def test_ordinary_verb_is_not_intercepted(self) -> None:
        self.assertNotIn(server._resolve_verb(self.game, "look"), server._INTERCEPTED_VERBS)


class TestChoiceCaseInsensitive(unittest.TestCase):
    """B2: CHOICE answers must grade case-insensitively, like SEQUENCE does."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_uppercase_choice_is_accepted(self) -> None:
        verdict = self.registry.evaluate("virus_signature_match", "BOOT_SECTOR_VIRUS")
        self.assertTrue(verdict.correct)

    def test_mixedcase_clean_is_accepted(self) -> None:
        verdict = self.registry.evaluate("signature_near_miss", "Clean")
        self.assertTrue(verdict.correct)

    def test_wrong_choice_still_rejected(self) -> None:
        verdict = self.registry.evaluate("virus_signature_match", "rootkit_virus")
        self.assertFalse(verdict.correct)


class TestAllVirusesFoundDerived(unittest.TestCase):
    """B3: all_viruses_found must reflect found_viruses regardless of which
    scan variant found the last virus."""

    def test_false_until_all_found(self) -> None:
        game = build_real_game()
        game.player.found_viruses = list(VIRUS_TYPES[:-1])
        self.assertFalse(game.all_viruses_found)
        self.assertFalse(game.snapshot()["all_viruses_found"])

    def test_true_when_all_found_via_any_path(self) -> None:
        game = build_real_game()
        # Simulate the last virus being recorded by a targeted scan path,
        # which historically never set the flag.
        for virus in VIRUS_TYPES:
            game.player._record_virus_found(virus)
        self.assertTrue(game.all_viruses_found)
        self.assertTrue(game.snapshot()["all_viruses_found"])


class TestTakeFromContainer(unittest.TestCase):
    """B4: taking a nested item must add it to inventory, not destroy it."""

    def test_take_nested_item_lands_in_inventory(self) -> None:
        game = build_real_game()
        room = game.player.location
        room.items["toolbox"] = {"nested_widget": "A small widget inside the toolbox."}
        result = game.player.take("nested_widget")
        self.assertIn("nested_widget", game.player.items)
        self.assertNotIn("nested_widget", room.items["toolbox"])
        self.assertIn("Taken", result)


class TestDirtyFlagOnPrefixedReadOnly(unittest.TestCase):
    """B5: a read-only command typed as a prefix must not mark the game dirty."""

    def test_prefixed_readonly_verb_does_not_dirty(self) -> None:
        game = build_real_game()
        game.changes_since_save = False
        game.feed("know")  # prefix of the read-only 'knowledge' command
        self.assertFalse(game.changes_since_save)

    def test_mutating_command_still_dirties(self) -> None:
        game = build_real_game()
        game.changes_since_save = False
        game.feed("go north")
        self.assertTrue(game.changes_since_save)


class TestGatedRoomPuzzlesToleratesUnknownId(unittest.TestCase):
    """B6: an unknown puzzle id bound to a room must not crash the gate."""

    def test_unknown_binding_is_skipped(self) -> None:
        game = build_real_game()
        game.player.location.puzzles.append("no_such_puzzle_id")
        try:
            game._gated_room_puzzles()  # must not raise KeyError
        except KeyError:
            self.fail("_gated_room_puzzles raised KeyError on an unknown binding")


class TestMapFrameAccommodatesLowestComponent(unittest.TestCase):
    """B7: the fog frame must be tall enough for the lowest-placed component
    (pcie_x1_2 at row 57) so its marker is not clipped."""

    def test_frame_has_enough_interior_rows(self) -> None:
        game = build_real_game()
        rendered = render_map(game, game.map_grid)
        interior = [line for line in rendered.splitlines() if line.startswith("|")]
        # pcie_x1_2 sits at row 57, so at least 57 interior rows must exist.
        self.assertGreaterEqual(len(interior), 57)


class TestSuspiciousDecoyDoesNotRecordVirus(unittest.TestCase):
    """B8: a benign-but-suspicious decoy must not add a virus to found_viruses
    just because a keyword trips the type heuristic."""

    def test_decoy_with_keyword_records_nothing(self) -> None:
        game = build_real_game()
        room = game.player.location
        room.items["decoy_chip"] = "A suspicious chip mentioning the boot process."
        before = list(game.player.found_viruses)
        game.player._analyze_item_for_threats("decoy_chip", room.items["decoy_chip"])
        self.assertEqual(game.player.found_viruses, before)


if __name__ == "__main__":
    unittest.main()
