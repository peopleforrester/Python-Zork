#!/usr/bin/env python3
"""
Unit tests for helper utility functions
"""

import unittest

from computerquest.utils.helpers import prefix_match, truncate_desc


class TestHelpers(unittest.TestCase):
    """Test cases for the helper utility functions"""

    def test_prefix_match(self):
        """Test prefix matching utility"""
        # Test with complete match
        candidates = ["north", "south", "east", "west"]
        self.assertEqual(prefix_match("north", candidates), "north")

        # Test with unique prefix
        self.assertEqual(prefix_match("no", candidates), "north")
        self.assertEqual(prefix_match("ea", candidates), "east")

        # Test with ambiguous prefix (should return original)
        ambiguous_candidates = ["test", "testing", "tested"]
        self.assertEqual(prefix_match("test", ambiguous_candidates), "test")

        # Test with non-matching prefix
        self.assertEqual(prefix_match("xyz", candidates), "xyz")

        # Test with empty candidates
        self.assertEqual(prefix_match("test", []), "test")

        # Test with single-letter prefix (should return original)
        self.assertEqual(prefix_match("n", candidates), "n")

    def test_truncate_desc(self):
        """Test description truncation utility"""
        # Test simple case
        self.assertEqual(truncate_desc("Short text"), "Short text")

        # Test truncation
        long_text = "This is a very long text that should be truncated to fit the maximum length limit"
        truncated = truncate_desc(long_text, max_length=30)
        self.assertEqual(len(truncated), 30)
        self.assertTrue(truncated.endswith("..."))
        self.assertEqual(truncated, "This is a very long text th...")

        # Test sentence truncation
        sentence_text = "First sentence. Second sentence. Third sentence."
        sentence_trunc = truncate_desc(sentence_text)
        self.assertEqual(sentence_trunc, "First sentence")

        # Test with None input
        self.assertEqual(truncate_desc(None), "")

        # Test with empty string
        self.assertEqual(truncate_desc(""), "")


class TestAnsiColorGate(unittest.TestCase):
    """Step LP.2: ANSI escapes only render when stdout is a TTY."""

    def test_colors_empty_when_not_a_tty(self):
        """Tests capture stdout, so isatty() is False — escapes should be empty."""
        from computerquest.utils.helpers import Colors

        # When stdout isn't a TTY, every color attribute is an empty string
        # rather than an ANSI escape, keeping captured output grep-friendly.
        self.assertEqual(Colors.RESET, "")
        self.assertEqual(Colors.RED, "")
        self.assertEqual(Colors.GREEN, "")
        self.assertEqual(Colors.BOLD, "")


class TestIsVirusName(unittest.TestCase):
    """Step 4.3: canonical-name detection replaces the old substring sniff
    so non-virus items containing 'virus' in their name don't false-positive."""

    def test_canonical_virus_names_detected(self):
        from computerquest.config import VIRUS_TYPES, is_virus_name

        for canonical in VIRUS_TYPES:
            self.assertTrue(is_virus_name(canonical), canonical)

    def test_non_virus_with_virus_substring_not_detected(self):
        """The test fixture `virus_item` and `antivirus_tool` must not match."""
        from computerquest.config import is_virus_name

        self.assertFalse(is_virus_name("virus_item"))
        self.assertFalse(is_virus_name("antivirus_tool"))
        self.assertFalse(is_virus_name("test_virus"))

    def test_unrelated_strings_not_detected(self):
        from computerquest.config import is_virus_name

        self.assertFalse(is_virus_name(""))
        self.assertFalse(is_virus_name("cpu_package"))


class TestMotherboardSingleSource(unittest.TestCase):
    """Step 3.5: motherboard ASCII lives in one place. Game.display_motherboard
    and ComponentVisualizer.render_motherboard_layout_text must return the
    same string."""

    def test_renderers_agree(self):
        from computerquest.mechanics.visualizer import ComponentVisualizer
        from tests._helpers import build_real_game

        game = build_real_game()
        viz = ComponentVisualizer()

        self.assertEqual(
            game.display_motherboard(),
            viz.render_motherboard_layout_text(),
        )

    def test_diagram_contains_known_landmarks(self):
        from computerquest.mechanics.visualizer import ComponentVisualizer

        diagram = ComponentVisualizer().render_motherboard_layout_text()
        for landmark in ("CPU Package", "L3 Cache", "RAM DIMM", "PCH", "Virus Locations"):
            self.assertIn(landmark, diagram)


class TestStatusBarReadsRealPlayer(unittest.TestCase):
    """Step 3.6: format_look_output's status bar must reflect the real
    player's health and inventory size, not hardcoded placeholders."""

    def _build_inputs(self):
        from computerquest.models.component import Component
        from computerquest.models.player import Player

        location = Component(name="Test Loc", description="for status-bar test")
        player = Player(location=location, items={"a": "x", "b": "y"}, name="Tester")
        return location, player

    def test_health_bar_reflects_player_state(self):
        from computerquest.config import INVENTORY_LIMIT
        from computerquest.utils.helpers import format_look_output

        location, player = self._build_inputs()
        player.health = 7  # below the green/yellow threshold

        out = format_look_output(
            location=location,
            connections=location.doors,
            items=list(location.items.keys()),
            player=player,
        )
        self.assertIn(f"7/{player.max_health}", out)
        self.assertIn(f"2/{INVENTORY_LIMIT}", out)  # two seeded items

    def test_status_bar_falls_back_when_player_is_none(self):
        from computerquest.config import INVENTORY_LIMIT, MAX_HEALTH
        from computerquest.utils.helpers import format_look_output

        location, _ = self._build_inputs()
        out = format_look_output(
            location=location,
            connections=location.doors,
            items=[],
        )
        self.assertIn(f"{MAX_HEALTH}/{MAX_HEALTH}", out)
        self.assertIn(f"0/{INVENTORY_LIMIT}", out)


if __name__ == "__main__":
    unittest.main()
