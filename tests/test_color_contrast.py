#!/usr/bin/env python3
"""
ABOUTME: Terminal colours stay on the bright ANSI set for contrast (issue #9).
ABOUTME: The no-colour path must stay byte-identical, since goldens pin it.
"""

import re
import unittest

from computerquest.utils.helpers import Colors
from tests._helpers import build_real_game

# Standard-intensity foregrounds. Dim on a near-black terminal; blue especially.
DIM_FOREGROUND = re.compile(r"\x1b\[(?:0;)?3[0-7]m")
BRIGHT_FOREGROUND = re.compile(r"\x1b\[9[0-7]m")


class TestPaletteIsBright(unittest.TestCase):
    def test_every_defined_colour_is_bright(self):
        for name in ("RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE"):
            with self.subTest(colour=name):
                code = getattr(Colors, name)
                if not code:
                    continue  # colour disabled in this environment
                self.assertRegex(code, r"\x1b\[9[0-7]m")

    def test_no_unusable_black_is_offered(self):
        """There is no legible black on this background, so the constant is
        gone rather than left available to reach for."""
        self.assertFalse(hasattr(Colors, "BLACK"))

    def test_bold_is_still_available_as_a_separate_lever(self):
        """Brightness comes from the colour, so BOLD stays free for emphasis."""
        self.assertTrue(hasattr(Colors, "BOLD"))


class TestEmittedTextUsesBrightColours(unittest.TestCase):
    """Guards against a dim code drifting back in via a literal escape."""

    def setUp(self):
        self.game = build_real_game()

    def _emit(self):
        parts = []
        for command in ("look", "help", "knowledge", "status", "objectives",
                        "inventory", "map", "achievements"):
            parts.append(self.game.feed(command))
        return "\n".join(parts)

    def test_no_dim_foreground_is_emitted(self):
        text = self._emit()
        found = DIM_FOREGROUND.findall(text)
        self.assertEqual(found, [], f"dim ANSI foreground in output: {set(found)}")

    def test_colour_is_actually_being_emitted(self):
        """Otherwise the assertion above passes on colourless output."""
        if not Colors.GREEN:
            self.skipTest("colour disabled in this environment")
        self.assertRegex(self._emit(), BRIGHT_FOREGROUND.pattern)


class TestNoColourPathIsUnchanged(unittest.TestCase):
    """The golden fixtures pin help, welcome and topic text byte for byte with
    colour disabled, so the palette change must not reach them."""

    def test_disabled_colour_yields_no_escapes(self):
        if Colors.GREEN:
            self.skipTest("colour enabled in this environment")
        game = build_real_game()
        self.assertNotIn("\x1b[", game.feed("help"))


if __name__ == "__main__":
    unittest.main()
