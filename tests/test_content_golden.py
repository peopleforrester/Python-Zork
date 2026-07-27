#!/usr/bin/env python3
"""
ABOUTME: Characterization tests pinning the exact static-content output.
ABOUTME: Guards the game.py content extraction against any wording drift.
"""

import json
import unittest
from pathlib import Path

from tests._helpers import build_real_game

_GOLDEN = Path(__file__).parent / "fixtures" / "golden_content.json"


class TestStaticContentUnchanged(unittest.TestCase):
    """Help, welcome, and about-topic text must render byte-identically to the
    golden capture taken before the content was moved out of game.py."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = json.loads(_GOLDEN.read_text())
        cls.game = build_real_game()

    def test_help_text_matches_golden(self) -> None:
        self.assertEqual(self.game.show_help(), self.golden["help"])

    def test_welcome_text_matches_golden(self) -> None:
        self.assertEqual(self.game.welcome_text(), self.golden["welcome"])

    def test_every_component_topic_matches_golden(self) -> None:
        for topic, expected in self.golden["component_info"].items():
            with self.subTest(topic=topic):
                self.assertEqual(self.game.get_component_info(topic), expected)

    def test_golden_covers_the_real_topic_set(self) -> None:
        """The fixture must exercise every shipped topic, or the guard is weak."""
        for topic in ("cpu", "memory", "cache", "storage", "bus",
                      "network", "firmware", "gpu", "kernel", "virus"):
            self.assertIn(topic, self.golden["component_info"])
            # A real topic returns its article, not a not-found message.
            self.assertNotIn("not found", self.golden["component_info"][topic].lower())


if __name__ == "__main__":
    unittest.main()
