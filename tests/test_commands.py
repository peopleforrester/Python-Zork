#!/usr/bin/env python3
"""
Unit tests for the Command pattern implementation
"""

import unittest
from unittest.mock import patch, MagicMock
from computerquest.commands import (
    Command, MoveCommand, LookCommand, TakeCommand, DropCommand,
    InventoryCommand, ScanCommand, AdvancedScanCommand, AnalyzeCommand,
    QuarantineCommand, HelpCommand, MapCommand, ReadCommand, StatusCommand,
    CommandProcessor
)
from computerquest.models.component import Component
from computerquest.models.player import Player
from computerquest.config import VIRUS_TYPES

class TestCommandBase(unittest.TestCase):
    """Base class for command tests with common setup"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock game object
        self.game = MagicMock()
        
        # Create test component
        self.component = Component(
            name="Test Component",
            description="A test component",
            iden="TEST001"
        )
        
        # Create player with some test items
        self.player_items = {
            "test_item": "A test item for the player",
            "antivirus_tool": "A virus scanning tool"
        }
        
        self.player = Player(
            location=self.component,
            items=self.player_items,
            name="Test Player"
        )
        
        # Add items to the component
        self.component.add_items({
            "component_item": "An item in the component",
            "test_virus": "A test virus"
        })
        
        # Set up game.player
        self.game.player = self.player
        
        # Set up minimal game functions needed for commands
        self.game._match_item_prefix = lambda x: x  # Identity function
        self.game._match_inventory_item_prefix = lambda x: x  # Identity function
        self.game._match_command_prefix = lambda x: x  # Identity function
        self.game.progress = MagicMock()
        self.game.progress.update.return_value = []

class TestBaseCommand(TestCommandBase):
    """Test the base Command class"""
    
    def test_init(self):
        """Test initialization of base command"""
        cmd = Command(self.game, ["arg1", "arg2"])
        self.assertEqual(cmd.game, self.game)
        self.assertEqual(cmd.args, ["arg1", "arg2"])
        
        # Test with default args
        default_cmd = Command(self.game)
        self.assertEqual(default_cmd.args, [])
    
    def test_can_execute(self):
        """Test can_execute method"""
        cmd = Command(self.game)
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)
    
    def test_execute_not_implemented(self):
        """Test execute method raises NotImplementedError"""
        cmd = Command(self.game)
        with self.assertRaises(NotImplementedError):
            cmd.execute()

class TestMoveCommand(TestCommandBase):
    """Test the MoveCommand class"""
    
    def test_can_execute(self):
        """Test can_execute validation"""
        # Valid case
        cmd = MoveCommand(self.game, ["north"])
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)
        
        # Invalid case (no direction)
        invalid_cmd = MoveCommand(self.game, [])
        can_exec, error = invalid_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("direction", error)
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock move function
        self.game.move.return_value = "Moved to new location"
        
        # Execute command
        cmd = MoveCommand(self.game, ["north"])
        result = cmd.execute()
        
        # Check move was called with correct direction
        self.game.move.assert_called_once_with("north")
        self.assertEqual(result, "Moved to new location")

class TestLookCommand(TestCommandBase):
    """Test the LookCommand class"""
    
    def test_execute_no_args(self):
        """Test looking at current location"""
        # Set up mock look function
        self.player.look.return_value = "Location description"
        
        # Execute command without args
        cmd = LookCommand(self.game, [])
        result = cmd.execute()
        
        # Check player.look was called with no args
        self.player.look.assert_called_once_with()
        self.assertEqual(result, "Location description")
        
        # Check that location was marked as visited
        self.assertTrue(self.component.visited)
    
    def test_execute_with_item(self):
        """Test looking at a specific item"""
        # Set up mock look function with arg
        self.player.look.return_value = "Item description"
        
        # Execute command with arg
        cmd = LookCommand(self.game, ["test_item"])
        result = cmd.execute()
        
        # Check player.look was called with correct arg
        self.player.look.assert_called_with("test_item")
        self.assertEqual(result, "Item description")

class TestTakeCommand(TestCommandBase):
    """Test the TakeCommand class"""
    
    def test_can_execute(self):
        """Test can_execute validation"""
        # Valid case
        cmd = TakeCommand(self.game, ["component_item"])
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)
        
        # Invalid case (no item)
        invalid_cmd = TakeCommand(self.game, [])
        can_exec, error = invalid_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("take", error)
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock take function
        self.player.take.return_value = "Taken: component_item"
        
        # Execute command
        cmd = TakeCommand(self.game, ["component_item"])
        result = cmd.execute()
        
        # Check take was called correctly
        self.player.take.assert_called_once_with("component_item")
        self.assertEqual(result, "Taken: component_item")
        
        # Check turn counter increased
        self.assertEqual(self.game.turns, 1)

class TestDropCommand(TestCommandBase):
    """Test the DropCommand class"""
    
    def test_can_execute(self):
        """Test can_execute validation"""
        # Valid case with existing item
        self.game._match_inventory_item_prefix.return_value = "test_item"
        cmd = DropCommand(self.game, ["test_item"])
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)
        
        # Invalid case (no item)
        invalid_cmd = DropCommand(self.game, [])
        can_exec, error = invalid_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("drop", error)
        
        # Invalid case (non-existent item)
        self.game._match_inventory_item_prefix.return_value = "nonexistent"
        invalid_item_cmd = DropCommand(self.game, ["nonexistent"])
        can_exec, error = invalid_item_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("don't have", error)
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock drop function
        self.player.drop.return_value = "Dropped: test_item"
        self.game._match_inventory_item_prefix.return_value = "test_item"
        
        # Execute command
        cmd = DropCommand(self.game, ["test_item"])
        result = cmd.execute()
        
        # Check drop was called correctly
        self.player.drop.assert_called_once_with("test_item")
        self.assertEqual(result, "Dropped: test_item")
        
        # Check turn counter increased
        self.assertEqual(self.game.turns, 1)

class TestInventoryCommand(TestCommandBase):
    """Test the InventoryCommand class"""
    
    def test_execute_empty(self):
        """Test with empty inventory"""
        # Empty the player's inventory
        self.player.items = {}
        
        # Execute command
        cmd = InventoryCommand(self.game)
        result = cmd.execute()
        
        # Check result indicates empty inventory
        self.assertIn("empty", result.lower())
    
    def test_execute_with_items(self):
        """Test with items in inventory"""
        # Execute command
        cmd = InventoryCommand(self.game)
        result = cmd.execute()
        
        # Check result lists items
        self.assertIn("System Storage Contains", result)
        self.assertIn("test_item", result)
        self.assertIn("antivirus_tool", result)

class TestScanCommand(TestCommandBase):
    """Test the ScanCommand class"""
    
    def test_execute_no_args(self):
        """Test scanning current location"""
        # Set up mock scan function
        self.player.scan.return_value = "Scan complete. No viruses detected."
        
        # Execute command
        cmd = ScanCommand(self.game)
        result = cmd.execute()
        
        # Check scan was called correctly
        self.player.scan.assert_called_once_with()
        self.assertEqual(result, "Scan complete. No viruses detected.")
        
        # Check turn counter increased
        self.assertEqual(self.game.turns, 1)
    
    def test_execute_with_item(self):
        """Test scanning a specific item"""
        # Set up mock scan function
        self.player.scan.return_value = "No virus detected in item."
        
        # Execute command
        cmd = ScanCommand(self.game, ["component_item"])
        result = cmd.execute()
        
        # Check scan was called with correct arg
        self.player.scan.assert_called_once_with("component_item")
        self.assertEqual(result, "No virus detected in item.")
    
    def test_execute_finds_all_viruses(self):
        """Test when all viruses are found"""
        # Set all viruses as found
        self.player.found_viruses = VIRUS_TYPES.copy()
        
        # Set up mock scan function
        self.player.scan.return_value = "All viruses found!"
        
        # Execute command
        cmd = ScanCommand(self.game)
        result = cmd.execute()
        
        # Check all_viruses_found flag is set
        self.assertTrue(self.game.all_viruses_found)

class TestQuarantineCommand(TestCommandBase):
    """Test the QuarantineCommand class"""
    
    def test_can_execute(self):
        """Test can_execute validation"""
        # Valid case
        cmd = QuarantineCommand(self.game, ["test_virus"])
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)
        
        # Invalid case (no virus specified)
        invalid_cmd = QuarantineCommand(self.game, [])
        can_exec, error = invalid_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("which virus", error.lower())
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock quarantine function
        self.player.quarantine.return_value = "Success! Virus quarantined."
        
        # Execute command
        cmd = QuarantineCommand(self.game, ["test_virus"])
        result = cmd.execute()
        
        # Check quarantine was called correctly
        self.player.quarantine.assert_called_once_with("test_virus")
        self.assertEqual(result, "Success! Virus quarantined.")
        
        # Check turn counter increased
        self.assertEqual(self.game.turns, 1)
    
    def test_execute_victory_condition(self):
        """Test victory condition when all viruses quarantined"""
        # Setup quarantined viruses and mock functions
        self.player.quarantined_viruses = VIRUS_TYPES.copy()
        self.player.quarantine.return_value = "Success! Virus quarantined."
        self.game.victory_message.return_value = "Victory message!"
        
        # Execute command
        cmd = QuarantineCommand(self.game, ["test_virus"])
        result = cmd.execute()
        
        # Check victory condition set
        self.assertTrue(self.game.victory)
        self.assertTrue(self.game.game_over)
        self.assertIn("Success! Virus quarantined.", result)
        self.assertIn("Victory message!", result)

class TestHelpCommand(TestCommandBase):
    """Test the HelpCommand class"""
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock show_help function
        self.game.show_help.return_value = "Help text"
        
        # Execute command
        cmd = HelpCommand(self.game)
        result = cmd.execute()
        
        # Check show_help was called
        self.game.show_help.assert_called_once()
        self.assertEqual(result, "Help text")

class TestMapCommand(TestCommandBase):
    """Test the MapCommand class"""
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock display_map function
        self.game.display_map.return_value = "ASCII map"
        
        # Execute command
        cmd = MapCommand(self.game)
        result = cmd.execute()
        
        # Check display_map was called
        self.game.display_map.assert_called_once()
        self.assertEqual(result, "ASCII map")

class TestReadCommand(TestCommandBase):
    """Test the ReadCommand class"""
    
    def test_can_execute(self):
        """Test can_execute validation"""
        # Valid case
        cmd = ReadCommand(self.game, ["test_item"])
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)
        
        # Invalid case (no item)
        invalid_cmd = ReadCommand(self.game, [])
        can_exec, error = invalid_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("read", error.lower())
    
    def test_execute_inventory_item(self):
        """Test reading inventory item"""
        # Execute command for inventory item
        cmd = ReadCommand(self.game, ["test_item"])
        result = cmd.execute()
        
        # Check result matches item description
        self.assertEqual(result, "A test item for the player")
    
    def test_execute_room_item(self):
        """Test reading room item"""
        # Execute command for room item
        cmd = ReadCommand(self.game, ["component_item"])
        result = cmd.execute()
        
        # Check result matches item description
        self.assertEqual(result, "An item in the component")
    
    def test_execute_formatted_item(self):
        """Test reading a formatted document (starting with #)"""
        # Add formatted document
        self.player.items["document"] = "# Document Title\n\nThis is a document with formatting."
        
        # Execute command
        cmd = ReadCommand(self.game, ["document"])
        result = cmd.execute()
        
        # Check formatting was handled correctly
        self.assertEqual(result, "Document Title\n\nThis is a document with formatting.")
    
    def test_execute_nonexistent_item(self):
        """Test reading non-existent item"""
        # Execute command for non-existent item
        cmd = ReadCommand(self.game, ["nonexistent"])
        result = cmd.execute()
        
        # Check error message
        self.assertIn("no nonexistent to read", result.lower())

class TestStatusCommand(TestCommandBase):
    """Test the StatusCommand class"""
    
    def test_execute(self):
        """Test execute method"""
        # Set up mock check_progress function
        self.player.check_progress.return_value = "Progress report"
        
        # Execute command
        cmd = StatusCommand(self.game)
        result = cmd.execute()
        
        # Check check_progress was called
        self.player.check_progress.assert_called_once()
        self.assertEqual(result, "Progress report")

class TestCommandProcessor(TestCommandBase):
    """Test the CommandProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        
        # Create command processor
        self.command_processor = CommandProcessor(self.game)
    
    def test_init(self):
        """Test initialization"""
        # Check game reference
        self.assertEqual(self.command_processor.game, self.game)
        
        # Check commands dictionary contains all expected commands
        command_classes = [
            'go', 'move', 'north', 'n', 'south', 's', 'east', 'e', 'west', 'w',
            'northeast', 'ne', 'northwest', 'nw', 'southeast', 'se', 'southwest', 'sw',
            'up', 'u', 'down', 'd', 'look', 'examine', 'ex', 'take', 'get', 'drop',
            'inventory', 'i', 'scan', 'sc', 'advscan', 'advanced-scan', 'advanced_scan',
            'analyze', 'quarantine', 'help', 'quit', 'exit', 'q', 'map', 'm',
            'motherboard', 'mb', 'read', 'about', 'status', 'progress', 'knowledge',
            'achievements', 'achieve', 'stats', 'save', 'load', 'saves', 'listsaves',
            'deletesave', 'visualize', 'viz', 'simulate', 'sim'
        ]
        
        for cmd in command_classes:
            self.assertIn(cmd, self.command_processor.commands)
    
    def test_direction_command_factory(self):
        """Test direction command factory"""
        # Get a factory for a direction command
        north_factory = self.command_processor._direction_command('north')
        
        # Create a command using the factory
        cmd = north_factory(self.game)
        
        # Check it's a MoveCommand with the correct direction
        self.assertIsInstance(cmd, MoveCommand)
        self.assertEqual(cmd.args, ['north'])
    
    def test_process_valid_command(self):
        """Test processing a valid command"""
        # Mock the execution result
        mock_cmd = MagicMock()
        mock_cmd.can_execute.return_value = (True, None)
        mock_cmd.execute.return_value = "Command executed successfully"
        
        # Mock the command class
        mock_cmd_class = MagicMock(return_value=mock_cmd)
        self.command_processor.commands['test'] = mock_cmd_class
        
        # Process the command
        result = self.command_processor.process("test arg1 arg2")
        
        # Check command was created and executed correctly
        mock_cmd_class.assert_called_once_with(self.game, ['arg1', 'arg2'])
        mock_cmd.can_execute.assert_called_once()
        mock_cmd.execute.assert_called_once()
        self.assertEqual(result, "Command executed successfully")
    
    def test_process_invalid_command(self):
        """Test processing an invalid command"""
        # Process non-existent command
        result = self.command_processor.process("nonexistent")
        
        # Check error message
        self.assertIn("not recognized", result)
    
    def test_process_validation_failure(self):
        """Test command that fails validation"""
        # Mock a command that fails validation
        mock_cmd = MagicMock()
        mock_cmd.can_execute.return_value = (False, "Validation error")
        
        # Mock the command class
        mock_cmd_class = MagicMock(return_value=mock_cmd)
        self.command_processor.commands['test'] = mock_cmd_class
        
        # Process the command
        result = self.command_processor.process("test")
        
        # Check validation error was returned
        self.assertEqual(result, "Validation error")
        mock_cmd.execute.assert_not_called()  # Execute should not be called
    
    def test_process_empty_input(self):
        """Test processing empty input"""
        result = self.command_processor.process("")
        self.assertIn("Please enter a command", result)
    
    def test_process_with_achievements(self):
        """Test processing with new achievements"""
        # Mock a command
        mock_cmd = MagicMock()
        mock_cmd.can_execute.return_value = (True, None)
        mock_cmd.execute.return_value = "Command executed"
        
        # Mock the command class
        mock_cmd_class = MagicMock(return_value=mock_cmd)
        self.command_processor.commands['test'] = mock_cmd_class
        
        # Mock achievements
        achievement1 = MagicMock()
        achievement1.name = "Achievement 1"
        achievement1.description = "First achievement"
        
        achievement2 = MagicMock()
        achievement2.name = "Achievement 2"
        achievement2.description = "Second achievement"
        
        self.game.progress.update.return_value = [achievement1, achievement2]
        
        # Process the command
        result = self.command_processor.process("test")
        
        # Check result includes achievements
        self.assertIn("Command executed", result)
        self.assertIn("ACHIEVEMENT UNLOCKED", result)
        self.assertIn("Achievement 1", result)
        self.assertIn("First achievement", result)
        self.assertIn("Achievement 2", result)
        self.assertIn("Second achievement", result)


class TestHotkeyBindings(TestCommandBase):
    """Regression tests for command-key bindings.

    Guards against silent dict-key collisions where the same hotkey is bound to
    two different commands (only the last write wins, and the documented one
    breaks).
    """

    def setUp(self):
        super().setUp()
        self.command_processor = CommandProcessor(self.game)

    def test_s_resolves_to_south_movement(self):
        """`s` must invoke a south MoveCommand, not ScanCommand."""
        factory = self.command_processor.commands['s']
        cmd = factory(self.game)
        self.assertIsInstance(cmd, MoveCommand)
        self.assertEqual(cmd.args, ['south'])

    def test_sc_resolves_to_scan(self):
        """`sc` is the short form for scan after rebinding off `s`."""
        self.assertIs(self.command_processor.commands['sc'], ScanCommand)

    def test_scan_long_form_still_resolves_to_scan(self):
        """`scan` long form must continue to resolve to ScanCommand."""
        self.assertIs(self.command_processor.commands['scan'], ScanCommand)

if __name__ == "__main__":
    unittest.main()