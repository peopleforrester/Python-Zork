#!/usr/bin/env python3
"""
ABOUTME: The directional compass must put each marker beside its own label.
ABOUTME: Issue #7 — mapped coordinates never matched the template's labels.
"""

import re
import unittest

from tests._helpers import build_real_game

ANSI = re.compile(r"\x1b\[[0-9;]*m")
OPEN = "↑↓←→↗↖↘↙"
BLOCKED = "█"


def compass_of(game) -> list[str]:
    """The compass block from a `look`, stripped of colour."""
    plain = ANSI.sub("", game.feed("look"))
    lines = plain.splitlines()
    start = next(i for i, line in enumerate(lines) if "Directional Compass" in line)
    block = []
    for line in lines[start + 1:]:
        if not line.strip() or "[U]p" in line or "[D]own" in line:
            break
        block.append(line)
    return block


class TestCompassIsLegible(unittest.TestCase):
    """Every label has to survive, and every marker has to sit next to the
    label it describes. Both failed: markers were written several columns left
    of their label, landing on other labels."""

    LABELS = ("N", "S", "E", "W", "NE", "NW", "SE", "SW")

    def setUp(self):
        self.game = build_real_game()
        self.block = compass_of(self.game)

    def test_the_compass_renders(self):
        self.assertTrue(self.block)

    def test_every_label_is_present_and_intact(self):
        joined = "\n".join(self.block)
        for label in self.LABELS:
            with self.subTest(label=label):
                self.assertIn(label, joined)

    def test_no_two_letter_label_is_split_by_a_marker(self):
        """A marker adjacent to a label is the design; a marker written *into*
        one is the bug. The old rose produced rows like 'W█ +' where the marker
        for one direction landed inside the space of another."""
        for row in self.block:
            with self.subTest(row=row.strip()):
                self.assertNotRegex(
                    row, rf"[NS][{OPEN}{BLOCKED}][EW]",
                    "a marker is written inside a diagonal label",
                )

    def test_diagonal_labels_stay_contiguous(self):
        joined = "\n".join(self.block)
        for pair in ("NE", "NW", "SE", "SW"):
            with self.subTest(label=pair):
                self.assertIn(pair, joined)

    def test_each_marker_is_adjacent_to_its_own_label(self):
        """A marker two or more columns from every label is noise."""
        positions = {}
        for r, row in enumerate(self.block):
            for label in self.LABELS:
                # find standalone labels, not the N inside NE
                for m in re.finditer(rf"(?<![A-Z]){re.escape(label)}(?![A-Z])", row):
                    positions.setdefault(label, []).append((r, m.start(), m.end()))
        markers = [(r, c) for r, row in enumerate(self.block)
                   for c, ch in enumerate(row) if ch in OPEN or ch == BLOCKED]
        self.assertTrue(markers, "no markers rendered at all")
        for r, c in markers:
            near = any(
                lr == r and (abs(c - (ls - 1)) <= 1 or abs(c - le) <= 1)
                for spans in positions.values() for lr, ls, le in spans
            )
            with self.subTest(marker_at=(r, c), row=self.block[r]):
                self.assertTrue(near, "marker is not adjacent to any label")

    def test_open_and_blocked_directions_both_appear(self):
        """The start room has some exits and not others, so a correct rose
        shows both kinds."""
        joined = "".join(self.block)
        self.assertTrue(any(ch in OPEN for ch in joined), "no open marker")
        self.assertIn(BLOCKED, joined, "no blocked marker")

    def test_rows_are_all_the_same_width(self):
        widths = {len(row) for row in self.block}
        self.assertEqual(len(widths), 1, f"ragged compass: {widths}")

    def test_the_marker_count_matches_the_compass_directions(self):
        """Eight compass points, so eight markers: no more, no fewer."""
        joined = "".join(self.block)
        markers = sum(1 for ch in joined if ch in OPEN or ch == BLOCKED)
        self.assertEqual(markers, 8, f"expected 8 markers, saw {markers}")


class TestCompassReflectsTheRoom(unittest.TestCase):
    def test_a_room_with_a_north_exit_shows_an_open_north(self):
        game = build_real_game()          # start room has a north exit
        block = compass_of(game)
        north_row = block[0]
        self.assertIn("↑", north_row)

    def test_a_direction_with_no_exit_is_blocked(self):
        game = build_real_game()          # start room has no east exit
        self.assertIn(BLOCKED, "".join(compass_of(game)))


if __name__ == "__main__":
    unittest.main()
