#!/usr/bin/env python3
"""
Unit tests for helper utility functions
"""

import unittest

from computerquest.utils.helpers import format_box, format_list, prefix_match, truncate_desc


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

    def test_format_box(self):
        """Test box formatting utility"""
        # Test simple box
        result = format_box("Test Title", "Test content")
        lines = result.strip().split('\n')

        # Check box structure
        self.assertEqual(len(lines), 5)  # Top border, title, separator, content, bottom border
        self.assertTrue(lines[0].startswith('+') and lines[0].endswith('+'))  # Top border
        self.assertTrue(lines[1].startswith('|') and lines[1].endswith('|'))  # Title line
        self.assertTrue("Test Title" in lines[1])  # Title content
        self.assertTrue(lines[2].startswith('+') and lines[2].endswith('+'))  # Separator
        self.assertTrue(lines[3].startswith('|') and lines[3].endswith('|'))  # Content line
        self.assertTrue("Test content" in lines[3])  # Content
        self.assertTrue(lines[4].startswith('+') and lines[4].endswith('+'))  # Bottom border

        # Test multi-line content
        multi_result = format_box("Multi Title", "Line 1\nLine 2\nLine 3")
        multi_lines = multi_result.strip().split('\n')

        # Check structure with multiple content lines
        self.assertEqual(len(multi_lines), 7)  # Top, title, separator, 3 content lines, bottom
        self.assertTrue("Line 1" in multi_lines[3])
        self.assertTrue("Line 2" in multi_lines[4])
        self.assertTrue("Line 3" in multi_lines[5])

        # Test with custom width
        width_result = format_box("Width Test", "Content", width=30)
        width_lines = width_result.strip().split('\n')

        # Check width
        self.assertEqual(len(width_lines[0]), 32)  # +30 chars+

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

    def test_format_list(self):
        """Test list formatting utility"""
        # Test with standard list
        items = ["Apple", "Banana", "Cherry"]
        formatted = format_list(items)
        expected = "- Apple\n- Banana\n- Cherry"
        self.assertEqual(formatted, expected)

        # Test with custom prefix
        formatted_custom = format_list(items, prefix="* ")
        expected_custom = "* Apple\n* Banana\n* Cherry"
        self.assertEqual(formatted_custom, expected_custom)

        # Test with empty list
        self.assertEqual(format_list([]), "")

        # Test with None
        self.assertEqual(format_list(None), "")

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
