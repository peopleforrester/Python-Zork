#!/usr/bin/env python3
"""
Unit tests for the Component class
"""

import unittest

from computerquest.models.component import Component


class TestComponent(unittest.TestCase):
    """Test cases for the Component class"""

    def setUp(self):
        """Set up test fixtures"""
        self.comp = Component(
            name="Test Component",
            description="A test component",
            lit=True,
            iden="TEST001"
        )

        # Create additional components for connection tests
        self.north_comp = Component(name="North Component", iden="NORTH001")
        self.east_comp = Component(name="East Component", iden="EAST001")
        self.special_comp = Component(name="Special Component", iden="SPECIAL001")

    def test_init(self):
        """Test component initialization"""
        # Test basic attributes
        self.assertEqual(self.comp.name, "Test Component")
        self.assertEqual(self.comp.desc, "A test component")
        self.assertEqual(self.comp.desc1, "A test component")
        self.assertEqual(self.comp.id, "TEST001")
        self.assertTrue(self.comp.lit)
        self.assertFalse(self.comp.save)

        # Test default collections
        self.assertEqual(self.comp.door, {})
        self.assertEqual(self.comp.doors, {})
        self.assertEqual(self.comp.openDoors, [])
        self.assertEqual(self.comp.items, {})
        self.assertEqual(self.comp.play, [])

        # Test default performance settings
        self.assertEqual(self.comp.security_level, 0)
        self.assertEqual(self.comp.data_types, [])
        self.assertEqual(self.comp.performance["speed"], 0)
        self.assertEqual(self.comp.performance["capacity"], 0)
        self.assertEqual(self.comp.performance["reliability"], 0)

        # Test state variables
        self.assertFalse(self.comp.visited)
        self.assertEqual(self.comp.power_state, "on")
        self.assertIsNone(self.comp.error_state)

    def test_set_specs(self):
        """Test setting component specifications"""
        self.comp.set_specs(
            security=2,
            data_types=["text", "binary"],
            speed=8,
            capacity=5,
            reliability=7
        )

        self.assertEqual(self.comp.security_level, 2)
        self.assertEqual(self.comp.data_types, ["text", "binary"])
        self.assertEqual(self.comp.performance["speed"], 8)
        self.assertEqual(self.comp.performance["capacity"], 5)
        self.assertEqual(self.comp.performance["reliability"], 7)

        # Test with default data_types
        empty_comp = Component("Empty")
        empty_comp.set_specs(security=1)
        self.assertEqual(empty_comp.data_types, [])

    def test_connect_to(self):
        """Test connecting components"""
        # Connect to north
        self.comp.connect_to(self.north_comp, "n")

        # Check door mappings
        self.assertIn("n", self.comp.doors)
        self.assertEqual(self.comp.doors["n"], self.north_comp)

        # Check openDoors record
        self.assertEqual(len(self.comp.openDoors), 1)
        self.assertIn(self.north_comp, self.comp.openDoors[0])
        self.assertEqual(self.comp.openDoors[0][self.north_comp], "n")

        # Connect another direction
        self.comp.connect_to(self.east_comp, "e")
        self.assertEqual(len(self.comp.doors), 2)
        self.assertEqual(self.comp.doors["e"], self.east_comp)
        self.assertEqual(len(self.comp.openDoors), 2)

        # Test connecting to the same component again (should not duplicate)
        self.comp.connect_to(self.north_comp, "n")
        self.assertEqual(len(self.comp.openDoors), 2)  # Should not add a duplicate

    def test_add_items(self):
        """Test adding items to the component"""
        items = {
            "test_item": "A test item description",
            "another_item": "Another item description"
        }

        self.comp.add_items(items)

        # Check items were added
        self.assertEqual(len(self.comp.items), 2)
        self.assertEqual(self.comp.items["test_item"], "A test item description")
        self.assertEqual(self.comp.items["another_item"], "Another item description")

        # Add more items
        more_items = {"third_item": "A third item"}
        self.comp.add_items(more_items)

        # Check items were added to existing set
        self.assertEqual(len(self.comp.items), 3)
        self.assertEqual(self.comp.items["third_item"], "A third item")

    def test_add_door(self):
        """Test adding a special door connection"""
        self.comp.add_door("Secure", "s", "n", self.special_comp)

        # Check door added to special door dict
        self.assertIn("Secure", self.comp.door)
        self.assertEqual(self.comp.door["Secure"][0], "s")  # Direction from this component
        self.assertEqual(self.comp.door["Secure"][1], self.special_comp)  # The component to connect to
        self.assertEqual(self.comp.door["Secure"][2], "n")  # Direction from other component

        # Check description was updated
        self.assertIn("connection", self.comp.desc.lower())
        self.assertIn("Secure", self.comp.desc)

    def test_print_details(self):
        """Test generating component details"""
        # Connect two directions for compass display
        self.comp.connect_to(self.north_comp, "n")
        self.comp.connect_to(self.east_comp, "e")

        # Add an item
        self.comp.add_items({"test_item": "A test item"})

        # Get details
        details = self.comp.print_details()

        # Check key elements in the output
        self.assertIn(self.comp.name, details)
        self.assertIn(self.comp.desc, details)
        self.assertIn("AVAILABLE CONNECTIONS", details)
        self.assertIn(f"N: {self.north_comp.name}", details)
        self.assertIn(f"E: {self.east_comp.name}", details)
        self.assertIn("COMPONENTS PRESENT", details)
        self.assertIn("test_item", details)

        # Check unvisited hint appears
        self.assertIn("scan", details.lower())

        # Now mark as visited and check for technical details
        self.comp.mark_visited()
        details_visited = self.comp.print_details()
        self.assertIn("TECHNICAL DETAILS", details_visited)

    def test_mark_visited(self):
        """Test marking a component as visited"""
        self.assertFalse(self.comp.visited)
        self.comp.mark_visited()
        self.assertTrue(self.comp.visited)

    def test_error_and_repair(self):
        """Test error state and repair functionality"""
        original_desc = self.comp.desc

        # Set error
        self.comp.error("Test Error Condition")

        # Check error state
        self.assertEqual(self.comp.error_state, "Test Error Condition")
        self.assertIn("ERROR:", self.comp.desc)
        self.assertIn("Test Error Condition", self.comp.desc)

        # Repair
        self.comp.repair()

        # Check repaired state
        self.assertIsNone(self.comp.error_state)
        self.assertEqual(self.comp.desc, original_desc)

if __name__ == "__main__":
    unittest.main()
