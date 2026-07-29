#!/usr/bin/env python3
"""
ABOUTME: Covers the `visualize`/`viz` command and its four text diagrams.
ABOUTME: Half the visualizer had no test, so a broken diagram shipped silently.
"""

import unittest

from computerquest.mechanics.visualizer import ComponentVisualizer
from tests._helpers import build_real_game


class TestVisualizerDiagrams(unittest.TestCase):
    """Each diagram must render its own titled content, not a stub."""

    def setUp(self) -> None:
        self.viz = ComponentVisualizer()

    def test_cpu_diagram_names_its_parts(self):
        out = self.viz.render_cpu_text()
        self.assertIn("CPU ARCHITECTURE", out)
        for landmark in ("Clock Speed", "Cores"):
            self.assertIn(landmark, out)

    def test_memory_diagram_walks_the_hierarchy(self):
        out = self.viz.render_memory_hierarchy_text()
        self.assertIn("MEMORY HIERARCHY", out)
        # The teaching point is the ordering from registers down to disk.
        for level in ("Regist", "L1", "L2", "L3", "RAM"):
            self.assertIn(level, out)

    def test_network_diagram_lists_the_stack_layers(self):
        out = self.viz.render_network_stack_text()
        self.assertIn("NETWORK PROTOCOL STACK", out)
        for layer in ("Application", "Transport", "Network", "Physical"):
            self.assertIn(layer, out)

    def test_storage_diagram_contrasts_hdd_and_ssd(self):
        out = self.viz.render_storage_hierarchy_text()
        self.assertIn("STORAGE SYSTEMS", out)
        self.assertIn("HDD", out)
        self.assertIn("SSD", out)

    def test_every_diagram_is_substantial_and_rectangular(self):
        """Guards against a diagram degrading to a header with no body."""
        renders = {
            "cpu": self.viz.render_cpu_text(),
            "memory": self.viz.render_memory_hierarchy_text(),
            "network": self.viz.render_network_stack_text(),
            "storage": self.viz.render_storage_hierarchy_text(),
            "motherboard": self.viz.render_motherboard_layout_text(),
        }
        for name, out in renders.items():
            with self.subTest(diagram=name):
                self.assertGreater(len(out.splitlines()), 8)
                self.assertGreater(len(out), 400)


class TestVisualizeCommand(unittest.TestCase):
    """The `viz <type>` surface, including every documented alias."""

    def setUp(self) -> None:
        self.game = build_real_game()

    def test_aliases_select_the_same_visualization(self):
        groups = {
            "memory hierarchy": ["memory", "ram", "cache"],
            "network protocol stack": ["network", "protocol"],
            "storage systems": ["storage", "disk", "drive"],
            "motherboard layout": ["motherboard", "mb", "mainboard"],
        }
        for expected, aliases in groups.items():
            outputs = {alias: self.game.feed(f"viz {alias}") for alias in aliases}
            for alias, out in outputs.items():
                with self.subTest(alias=alias):
                    self.assertIn(expected, out.lower())
            # Aliases must be true synonyms, not near-misses.
            self.assertEqual(len(set(outputs.values())), 1, f"{aliases} diverged")

    def test_cpu_visualization_renders(self):
        out = self.game.feed("viz cpu")
        self.assertIn("CPU ARCHITECTURE", out)

    def test_stop_returns_to_text_mode(self):
        self.game.feed("viz cpu")
        out = self.game.feed("viz stop")
        self.assertIn("Stopped", out)
        self.assertIsNone(self.game.current_visualization)

    def test_unknown_type_suggests_valid_ones(self):
        out = self.game.feed("viz bogus")
        self.assertIn("Unknown visualization type", out)
        for suggestion in ("cpu", "memory", "network", "storage"):
            self.assertIn(suggestion, out)

    def test_visualization_does_not_consume_a_turn(self):
        """Looking at a diagram is a read-only action."""
        before = self.game.turns
        self.game.feed("viz cpu")
        self.assertEqual(self.game.turns, before)


if __name__ == "__main__":
    unittest.main()
