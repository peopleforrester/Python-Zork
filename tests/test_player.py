#!/usr/bin/env python3
"""
Unit tests for the Player class
"""

import unittest

from computerquest.config import MAX_KNOWLEDGE
from computerquest.models.component import Component
from computerquest.models.player import Player


class TestPlayer(unittest.TestCase):
    """Test cases for the Player class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create test components
        self.start_component = Component(
            name="Start Component",
            description="Starting location",
            iden="START001"
        )

        self.connected_component = Component(
            name="Connected Component",
            description="Connected location",
            iden="CONN001"
        )

        # Connect the components
        self.start_component.connect_to(self.connected_component, "n")
        self.connected_component.connect_to(self.start_component, "s")

        # Create player with some test items
        self.player_items = {
            "test_item": "A test item for the player",
            "antivirus_tool": "A virus scanning tool"
        }

        self.player = Player(
            location=self.start_component,
            items=self.player_items,
            name="Test Player"
        )

        # Add some items to the starting component
        self.start_component.add_items({
            "component_item": "An item in the component",
            "virus_item": "A suspicious item that might be a virus"
        })

    def test_init(self):
        """Test player initialization"""
        # Test basic attributes
        self.assertEqual(self.player.location, self.start_component)
        self.assertEqual(self.player.items, self.player_items)
        self.assertEqual(self.player.name, "Test Player")
        self.assertEqual(self.player.health, 20)
        self.assertEqual(self.player.max_health, 20)
        self.assertFalse(self.player.com)  # Not an NPC
        self.assertFalse(self.player.death)

        # Test default collections
        self.assertEqual(self.player.found_viruses, [])
        self.assertEqual(self.player.quarantined_viruses, [])

        # Test knowledge areas
        self.assertEqual(self.player.knowledge["cpu"], 0)
        self.assertEqual(self.player.knowledge["memory"], 0)
        self.assertEqual(self.player.knowledge["storage"], 0)
        self.assertEqual(self.player.knowledge["networking"], 0)
        self.assertEqual(self.player.knowledge["security"], 0)

        # Test NPC behavior
        npc = Player(
            location=self.start_component,
            items={},
            NPC=True,
            name="Test NPC"
        )

        self.assertTrue(npc.com)
        self.assertIn(npc, self.start_component.play)

    def test_str(self):
        """Test string representation"""
        self.assertEqual(str(self.player), "Test Player")

        # Test default name
        unnamed_player = Player(location=self.start_component)
        self.assertEqual(str(unnamed_player), "Security Program")

    def test_go(self):
        """Test player movement"""
        # Valid movement
        result = self.player.go("n")
        self.assertTrue(result)
        self.assertEqual(self.player.location, self.connected_component)

        # Move back
        result = self.player.go("s")
        self.assertTrue(result)
        self.assertEqual(self.player.location, self.start_component)

        # Invalid movement
        result = self.player.go("w")  # No connection in this direction
        self.assertFalse(result)
        self.assertEqual(self.player.location, self.start_component)

        # Test NPC movement
        npc = Player(
            location=self.start_component,
            items={},
            NPC=True,
            name="Test NPC"
        )

        # Before movement, NPC is in start_component's play list
        self.assertIn(npc, self.start_component.play)

        # Move NPC
        npc.go("n")

        # After movement, NPC should be in connected_component's play list
        self.assertIn(npc, self.connected_component.play)
        self.assertNotIn(npc, self.start_component.play)

    def test_look(self):
        """Test looking at location or items"""
        # Looking at current location
        location_desc = self.player.look()
        self.assertIn(self.start_component.name, location_desc)
        self.assertIn(self.start_component.desc, location_desc)

        # Looking at item in the room
        item_desc = self.player.look("component_item")
        self.assertIn("component_item", item_desc)
        self.assertIn("An item in the component", item_desc)
        self.assertIn("take component_item", item_desc)

        # Looking at item in inventory
        inv_item_desc = self.player.look("test_item")
        self.assertIn("test_item", inv_item_desc)
        self.assertIn("A test item for the player", inv_item_desc)
        self.assertIn("drop test_item", inv_item_desc)

        # Looking at non-existent item
        not_found_desc = self.player.look("nonexistent_item")
        self.assertIn("not found", not_found_desc.lower())

    def test_take(self):
        """Test taking items"""
        # Take an item from the current location
        result = self.player.take("component_item")
        self.assertIn("Taken", result)

        # Check item moved from location to inventory
        self.assertIn("component_item", self.player.items)
        self.assertNotIn("component_item", self.player.location.items)

        # Try to take a non-existent item
        not_found = self.player.take("nonexistent_item")
        self.assertIn("no", not_found.lower())

        # Test inventory limit
        # Add items to reach the limit
        for i in range(6):  # Already has 3 items, add 6 more to exceed limit of 8
            self.player.items[f"extra_item_{i}"] = f"Extra item {i}"

        # Try to take another item (should fail)
        full_inv_result = self.player.take("virus_item")
        self.assertIn("full", full_inv_result.lower())

    def test_drop(self):
        """Test dropping items"""
        # Drop an item from inventory
        result = self.player.drop("test_item")
        self.assertIn("Dropped", result)

        # Check item moved from inventory to location
        self.assertIn("test_item", self.player.location.items)
        self.assertNotIn("test_item", self.player.items)

        # Try to drop a non-existent item
        not_found = self.player.drop("nonexistent_item")
        self.assertIn("don't have", not_found.lower())

    def test_scan(self):
        """Test scanning for viruses"""
        # The shared setUp seeds 'virus_item' into the location, which the
        # current substring-based virus detector flags. Remove it so we can
        # exercise the clean-location path first.
        self.player.location.items.pop("virus_item", None)

        result = self.player.scan()
        self.assertIn("No viruses detected", result)

        # Add a known virus and re-scan
        self.player.location.add_items({"boot_sector_virus": "A dangerous virus"})
        virus_result = self.player.scan()
        self.assertIn("SECURITY ALERT", virus_result)
        self.assertIn("boot_sector_virus", virus_result)
        self.assertIn("boot_sector_virus", self.player.found_viruses)

        # Scan a specific item that's not a virus
        item_result = self.player.scan("component_item")
        self.assertIn("No virus detected", item_result)

        # Scan a specific virus item
        virus_item_result = self.player.scan("boot_sector_virus")
        self.assertIn("ALERT", virus_item_result)
        self.assertIn("boot_sector_virus", virus_item_result)

        # Scan non-existent item
        not_found = self.player.scan("nonexistent_item")
        self.assertIn("no", not_found.lower())

        # Test scan without antivirus tool
        player_without_tool = Player(location=self.start_component)
        no_tool_result = player_without_tool.scan()
        self.assertIn("need an antivirus tool", no_tool_result.lower())

    def test_advanced_scan(self):
        """Test advanced scanning"""
        # Add decoder tool required for advanced scan
        self.player.items["decoder_tool"] = "A tool for advanced scans"

        # Set up test component for different component types
        cpu_component = Component(name="CPU Core", description="A CPU component")

        # Testing with CPU component
        self.player.location = cpu_component

        # Should require CPU knowledge
        insufficient_knowledge = self.player.advanced_scan()
        self.assertIn("need more knowledge", insufficient_knowledge.lower())

        # Increase knowledge to required level
        self.player.knowledge["cpu"] = 2
        self.player.knowledge["security"] = 1

        # Now the scan should work
        advanced_result = self.player.advanced_scan()
        self.assertIn("Advanced scan complete", advanced_result)

        # Add suspicious item and test scanning it
        self.player.location.add_items({"suspicious_data": "This data has some malicious patterns"})

        item_scan = self.player.advanced_scan("suspicious_data")
        self.assertIn("suspicious_data", item_scan)

        # Test scanning non-existent item
        not_found = self.player.advanced_scan("nonexistent_item")
        self.assertIn("no", not_found.lower())

        # Test without required tools
        player_without_tools = Player(location=cpu_component)
        player_without_tools.knowledge["cpu"] = 5  # High knowledge

        no_tools_result = player_without_tools.advanced_scan()
        self.assertIn("need", no_tools_result.lower())

    def test_quarantine(self):
        """Test quarantining viruses"""
        # Add a virus to found_viruses and the room
        virus_name = "test_virus"
        self.player.found_viruses.append(virus_name)
        self.player.location.add_items({virus_name: "A test virus"})

        # Quarantine the virus
        result = self.player.quarantine(virus_name)
        self.assertIn("Success", result)

        # Check virus was quarantined
        self.assertIn(virus_name, self.player.quarantined_viruses)
        self.assertNotIn(virus_name, self.player.location.items)
        self.assertIn(f"quarantined_{virus_name}", self.player.location.items)

        # Try to quarantine already-quarantined virus
        already_done = self.player.quarantine(virus_name)
        self.assertIn("already been quarantined", already_done)

        # Try to quarantine non-existent virus
        not_found = self.player.quarantine("nonexistent_virus")
        self.assertIn("haven't detected", not_found.lower())

        # Test quarantine without antivirus tool
        player_without_tool = Player(location=self.start_component)
        player_without_tool.found_viruses.append("another_virus")

        no_tool_result = player_without_tool.quarantine("another_virus")
        self.assertIn("need an antivirus tool", no_tool_result.lower())

    def test_analyze(self):
        """Test analyzing items"""
        # Add decoder tool required for analysis
        self.player.items["decoder_tool"] = "A tool for detailed analysis"

        # Add various item types to test
        self.player.location.add_items({
            "system_log": "A log showing system activities with some suspicious entries",
            "calculation_data": "Data showing unusual calculation patterns",
            "network_packet": "Captured network traffic with strange patterns"
        })

        # Test analyzing a log
        log_result = self.player.analyze("system_log")
        self.assertIn("Analysis of system_log", log_result)
        self.assertIn("log", log_result.lower())

        # Test analyzing calculations
        calc_result = self.player.analyze("calculation_data")
        self.assertIn("Analysis of calculation_data", calc_result)
        self.assertIn("calculation", calc_result.lower())

        # Test analyzing packets
        packet_result = self.player.analyze("network_packet")
        self.assertIn("Analysis of network_packet", packet_result)
        self.assertIn("packet", packet_result.lower())

        # Test analyzing non-existent item
        not_found = self.player.analyze("nonexistent_item")
        self.assertIn("no", not_found.lower())

        # Test without required tool
        player_without_tool = Player(location=self.start_component)
        no_tool_result = player_without_tool.analyze("system_log")
        self.assertIn("need a decoder tool", no_tool_result.lower())

    def test_check_progress(self):
        """Test progress reporting"""
        # Add some viruses to the found and quarantined lists
        self.player.found_viruses = ["virus1", "virus2"]
        self.player.quarantined_viruses = ["virus1"]

        # Get progress report
        progress = self.player.check_progress()

        # Check for expected elements (header is rendered uppercase)
        self.assertIn("MISSION STATUS REPORT", progress)
        self.assertIn("Viruses Found:", progress)
        self.assertIn("2/5", progress)
        self.assertIn("virus1", progress)
        self.assertIn("virus2", progress)
        self.assertIn("Viruses Quarantined:", progress)
        self.assertIn("1/5", progress)

    def test_knowledge_report(self):
        """Test knowledge reporting"""
        # Set some knowledge levels
        self.player.knowledge["cpu"] = 3
        self.player.knowledge["memory"] = 1
        self.player.knowledge["security"] = 5  # Max level

        # Get knowledge report
        knowledge = self.player.knowledge_report()

        # Header is rendered uppercase
        self.assertIn("COMPUTER ARCHITECTURE KNOWLEDGE", knowledge)
        self.assertIn("Cpu: ★★★☆☆", knowledge)
        self.assertIn("Memory: ★☆☆☆☆", knowledge)
        self.assertIn("Security: ★★★★★", knowledge)
        self.assertIn(f"Total Knowledge: 9/{len(self.player.knowledge) * MAX_KNOWLEDGE}", knowledge)

    def test_component_knowledge_increase(self):
        """Test knowledge increase based on component type"""
        # Test CPU component
        cpu_component = Component(name="CPU Core", description="A CPU component")
        self.player.location = cpu_component

        self.player._increase_component_knowledge()
        self.assertEqual(self.player.knowledge["cpu"], 1)

        # Test memory component
        memory_component = Component(name="RAM Module", description="A memory component")
        self.player.location = memory_component

        self.player._increase_component_knowledge()
        self.assertEqual(self.player.knowledge["memory"], 1)

        # Test storage component
        storage_component = Component(name="SSD Drive", description="A storage component")
        self.player.location = storage_component

        self.player._increase_component_knowledge()
        self.assertEqual(self.player.knowledge["storage"], 1)

        # Test network component
        network_component = Component(name="Network Interface", description="A network component")
        self.player.location = network_component

        self.player._increase_component_knowledge()
        self.assertEqual(self.player.knowledge["networking"], 1)

if __name__ == "__main__":
    unittest.main()
