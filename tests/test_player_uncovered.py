#!/usr/bin/env python3
"""
ABOUTME: Covers Player paths the suite missed: inventory quarantine, advscan
ABOUTME: gating and hidden-threat reporting, and the analyze hint ladder.
"""

import unittest

from computerquest.models.component import Component
from computerquest.models.player import Player


def _player(**kw):
    room = Component(name="Test Room", description="a room for player tests")
    return Player(location=room, name="Tester", **kw), room


class TestQuarantineFromInventory(unittest.TestCase):
    """The inventory branch had no test, yet it shares one collapsed body with
    the room branch; only the wording and the container differ."""

    def setUp(self) -> None:
        self.player, self.room = _player()
        self.player.items["antivirus_tool"] = "The tool"
        self.player.found_viruses.append("boot_sector_virus")

    def test_quarantines_a_virus_held_in_inventory(self):
        self.player.items["boot_sector_virus"] = "A nasty one."
        result = self.player.quarantine("boot_sector_virus")

        self.assertIn("Success", result)
        self.assertIn("from your inventory", result)
        self.assertIn("boot_sector_virus", self.player.quarantined_viruses)
        # Removed from inventory and replaced there by the neutralized copy.
        self.assertNotIn("boot_sector_virus", self.player.items)
        self.assertIn("quarantined_boot_sector_virus", self.player.items)
        self.assertNotIn("quarantined_boot_sector_virus", self.room.items)

    def test_room_branch_omits_the_inventory_wording(self):
        self.room.items["boot_sector_virus"] = "A nasty one."
        result = self.player.quarantine("boot_sector_virus")

        self.assertIn("Success", result)
        self.assertNotIn("from your inventory", result)
        self.assertIn("quarantined_boot_sector_virus", self.room.items)

    def test_virus_found_but_present_nowhere(self):
        result = self.player.quarantine("boot_sector_virus")
        self.assertIn("not in this location", result)
        self.assertEqual(self.player.quarantined_viruses, [])

    def test_requires_the_antivirus_tool(self):
        player, room = _player()
        player.found_viruses.append("boot_sector_virus")
        room.items["boot_sector_virus"] = "A nasty one."
        self.assertIn("need an antivirus tool", player.quarantine("boot_sector_virus"))

    def test_undetected_virus_is_refused(self):
        self.room.items["rootkit_virus"] = "Hidden."
        self.assertIn("haven't detected", self.player.quarantine("rootkit_virus"))

    def test_double_quarantine_is_refused(self):
        self.room.items["boot_sector_virus"] = "A nasty one."
        self.player.quarantine("boot_sector_virus")
        self.assertIn("already been quarantined", self.player.quarantine("boot_sector_virus"))


class TestAdvancedScanGating(unittest.TestCase):
    """advscan needs both tools and enough knowledge; the refusals were dark.

    A generic room classifies as component type 'other', which carries no
    knowledge requirement, so tool-only fixtures reach the scan itself.
    """

    def _equipped(self):
        player, room = _player()
        player.items["antivirus_tool"] = "The AV tool"
        player.items["decoder_tool"] = "The decoder"
        return player, room

    def test_missing_antivirus_tool_is_reported_first(self):
        player, _ = _player()
        self.assertIn("need an antivirus tool", player.advanced_scan())

    def test_missing_decoder_tool_is_reported(self):
        player, _ = _player()
        player.items["antivirus_tool"] = "The AV tool"
        self.assertIn("decoder tool", player.advanced_scan().lower())

    def test_insufficient_knowledge_is_reported(self):
        player, room = _player()
        room.name = "RAM Module"  # classifies as a memory component
        player.items["antivirus_tool"] = "The AV tool"
        player.items["decoder_tool"] = "The decoder"
        player.knowledge["memory"] = 0
        self.assertIn("more knowledge of memory", player.advanced_scan())

    def test_location_scan_reports_hidden_threats(self):
        player, room = self._equipped()
        room.items["odd_blob"] = "A suspicious blob of data."
        out = player.advanced_scan()
        self.assertIn("odd_blob", out)
        self.assertIn("Suspicious items", out)

    def test_location_scan_when_nothing_is_wrong(self):
        player, _ = self._equipped()
        self.assertIn("No threats detected", player.advanced_scan())

    def test_item_scan_targets_a_missing_item(self):
        player, _ = self._equipped()
        self.assertIn("no ghost here", player.advanced_scan("ghost").lower())


class TestAnalyzeHints(unittest.TestCase):
    """analyze routes a suspicious item to a type-specific hint."""

    def setUp(self) -> None:
        self.player, self.room = _player()
        self.player.items["decoder_tool"] = "Required for analysis"

    def test_analysis_requires_the_decoder_tool(self):
        bare, room = _player()
        room.items["manual"] = "An ordinary reference manual."
        self.assertIn("need a decoder tool", bare.analyze("manual"))

    def test_clean_item_reports_no_suspicion(self):
        self.room.items["manual"] = "An ordinary reference manual."
        out = self.player.analyze("manual")
        self.assertIn("No suspicious patterns", out)

    def test_hint_ladder_matches_the_described_subsystem(self):
        cases = {
            "A suspicious boot record": "boot sector",
            "A suspicious kernel module": "rootkit",
            "A suspicious memory pattern": "memory-resident",
            "A suspicious firmware image": "firmware",
            "A suspicious network packet": "network traffic",
        }
        for desc, expected in cases.items():
            with self.subTest(desc=desc):
                self.assertIn(expected, self.player._get_virus_hint(desc))

    def test_suspicious_item_raises_a_security_alert(self):
        self.room.items["blob"] = "A suspicious boot record."
        out = self.player.analyze("blob")
        self.assertIn("SECURITY ALERT", out)
        self.assertIn("boot sector", out)

    def test_unmatched_suspicious_description_yields_no_hint(self):
        self.assertEqual(self.player._get_virus_hint("A suspicious widget"), "")


if __name__ == "__main__":
    unittest.main()
