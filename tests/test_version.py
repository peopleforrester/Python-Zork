#!/usr/bin/env python3
"""
ABOUTME: Verifies version metadata has a single source of truth.
ABOUTME: Step 2.2 derives __version__ and GAME_VERSION via importlib.metadata.
"""

import unittest
from importlib.metadata import version

import computerquest
from computerquest import config


class TestVersionSingleSource(unittest.TestCase):
    def test_package_version_matches_pyproject(self):
        """computerquest.__version__ matches the installed dist metadata."""
        self.assertEqual(computerquest.__version__, version("computerquest"))

    def test_config_version_matches_package_version(self):
        """config.GAME_VERSION mirrors computerquest.__version__."""
        self.assertEqual(config.GAME_VERSION, computerquest.__version__)

    def test_version_is_post_step12_bump(self):
        """Step 2.2 bumps to >= 1.1.1 to mark the Week-1 critical-bug shipment."""
        major, minor, patch = (int(x) for x in computerquest.__version__.split(".")[:3])
        self.assertGreaterEqual((major, minor, patch), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
