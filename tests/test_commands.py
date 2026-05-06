#!/usr/bin/env python3
"""
Unit tests for the Command pattern implementation
"""

import unittest
from unittest.mock import MagicMock, patch

from computerquest.commands import (
    Command,
    CommandProcessor,
    DropCommand,
    HelpCommand,
    InventoryCommand,
    LookCommand,
    MapCommand,
    MoveCommand,
    QuarantineCommand,
    ReadCommand,
    ScanCommand,
    SimulateCommand,
    StatusCommand,
    TakeCommand,
)
from computerquest.config import VIRUS_TYPES
from tests._helpers import build_real_game


class TestCommandBase(unittest.TestCase):
    """Base class for command tests using a real Game instance.

    The test fixture exercises real collaborators (Player, Component, world).
    The player's starting location (cpu_package) is the component under test;
    a few deterministic test items are seeded so legacy tests can reference
    predictable names without depending on the world-builder's content.
    """

    def setUp(self):
        """Set up test fixtures"""
        # Real Game with full ComputerArchitecture, Player, CommandProcessor.
        self.game = build_real_game()
        self.player = self.game.player

        # Use the player's real starting location as the component under test.
        self.component = self.player.location

        # Seed deterministic test items into the real player's inventory and
        # current location so legacy tests can still reference these names.
        self.player.items.update({
            "test_item": "A test item for the player",
        })
        self.component.add_items({
            "component_item": "An item in the component",
            "test_virus": "A test virus",
        })
        self.player_items = self.player.items

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
        with patch.object(self.game, 'move', return_value="Moved to new location") as mock_move:
            cmd = MoveCommand(self.game, ["north"])
            result = cmd.execute()
            mock_move.assert_called_once_with("north")
            self.assertEqual(result, "Moved to new location")

class TestLookCommand(TestCommandBase):
    """Test the LookCommand class"""

    def test_execute_no_args(self):
        """Test looking at current location"""
        with patch.object(self.player, 'look', return_value="Location description") as mock_look:
            cmd = LookCommand(self.game, [])
            result = cmd.execute()
            mock_look.assert_called_once_with()
            self.assertEqual(result, "Location description")
            self.assertTrue(self.component.visited)

    def test_execute_with_item(self):
        """Test looking at a specific item"""
        with patch.object(self.player, 'look', return_value="Item description") as mock_look:
            cmd = LookCommand(self.game, ["test_item"])
            result = cmd.execute()
            mock_look.assert_called_with("test_item")
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
        # Real Player.take exercises real inventory transfer.
        cmd = TakeCommand(self.game, ["component_item"])
        result = cmd.execute()
        self.assertEqual(result, "Taken: component_item")
        self.assertIn("component_item", self.player.items)
        self.assertNotIn("component_item", self.component.items)
        self.assertEqual(self.game.turns, 1)

class TestDropCommand(TestCommandBase):
    """Test the DropCommand class"""

    def test_can_execute(self):
        """Test can_execute validation"""
        # Valid case: test_item is seeded in player inventory; real prefix
        # matcher resolves it directly.
        cmd = DropCommand(self.game, ["test_item"])
        can_exec, _ = cmd.can_execute()
        self.assertTrue(can_exec)

        # Invalid case (no item)
        invalid_cmd = DropCommand(self.game, [])
        can_exec, error = invalid_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("drop", error)

        # Invalid case (non-existent item)
        invalid_item_cmd = DropCommand(self.game, ["nonexistent"])
        can_exec, error = invalid_item_cmd.can_execute()
        self.assertFalse(can_exec)
        self.assertIn("don't have", error)

    def test_execute(self):
        """Test execute method"""
        # Real Player.drop exercises real inventory transfer.
        cmd = DropCommand(self.game, ["test_item"])
        result = cmd.execute()
        self.assertEqual(result, "Dropped: test_item")
        self.assertNotIn("test_item", self.player.items)
        self.assertIn("test_item", self.component.items)
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
        cmd = InventoryCommand(self.game)
        result = cmd.execute()
        self.assertIn("SYSTEM STORAGE", result)
        self.assertIn("test_item", result)
        self.assertIn("antivirus_tool", result)

class TestScanCommand(TestCommandBase):
    """Test the ScanCommand class"""

    def test_execute_no_args(self):
        """Test scanning current location"""
        with patch.object(self.player, 'scan', return_value="Scan complete. No viruses detected.") as mock_scan:
            cmd = ScanCommand(self.game)
            result = cmd.execute()
            mock_scan.assert_called_once_with()
            self.assertEqual(result, "Scan complete. No viruses detected.")
            self.assertEqual(self.game.turns, 1)

    def test_execute_with_item(self):
        """Test scanning a specific item"""
        with patch.object(self.player, 'scan', return_value="No virus detected in item.") as mock_scan:
            cmd = ScanCommand(self.game, ["component_item"])
            result = cmd.execute()
            mock_scan.assert_called_once_with("component_item")
            self.assertEqual(result, "No virus detected in item.")

    def test_execute_finds_all_viruses(self):
        """Test when all viruses are found"""
        self.player.found_viruses = VIRUS_TYPES.copy()
        with patch.object(self.player, 'scan', return_value="All viruses found!"):
            cmd = ScanCommand(self.game)
            cmd.execute()
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
        with patch.object(self.player, 'quarantine', return_value="Success! Virus quarantined.") as mock_q:
            cmd = QuarantineCommand(self.game, ["test_virus"])
            result = cmd.execute()
            mock_q.assert_called_once_with("test_virus")
            self.assertEqual(result, "Success! Virus quarantined.")
            self.assertEqual(self.game.turns, 1)

    def test_execute_victory_condition(self):
        """Test victory condition when all viruses quarantined"""
        self.player.quarantined_viruses = VIRUS_TYPES.copy()
        with patch.object(self.player, 'quarantine', return_value="Success! Virus quarantined."), \
             patch.object(self.game, 'victory_message', return_value="Victory message!"):
            cmd = QuarantineCommand(self.game, ["test_virus"])
            result = cmd.execute()
        self.assertTrue(self.game.victory)
        self.assertTrue(self.game.game_over)
        self.assertIn("Success! Virus quarantined.", result)
        self.assertIn("Victory message!", result)

class TestHelpCommand(TestCommandBase):
    """Test the HelpCommand class"""

    def test_execute(self):
        """Test execute method"""
        with patch.object(self.game, 'show_help', return_value="Help text") as mock_help:
            cmd = HelpCommand(self.game)
            result = cmd.execute()
            mock_help.assert_called_once()
            self.assertEqual(result, "Help text")

class TestMapCommand(TestCommandBase):
    """Test the MapCommand class"""

    def test_execute(self):
        """Test execute method"""
        with patch.object(self.game, 'display_map', return_value="ASCII map") as mock_map:
            cmd = MapCommand(self.game)
            result = cmd.execute()
            mock_map.assert_called_once()
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
        with patch.object(self.player, 'check_progress', return_value="Progress report") as mock_cp:
            cmd = StatusCommand(self.game)
            result = cmd.execute()
            mock_cp.assert_called_once()
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
            'achievements', 'achieve', 'stats', 'visualize', 'viz', 'simulate', 'sim'
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

    def test_typo_suggests_close_match_via_difflib(self):
        """A near-miss typo should surface a difflib suggestion.

        Use 'iventory' (one missing letter) — close enough that difflib
        scores it above the 0.6 cutoff but not in the typo-correction
        preprocess table.
        """
        result = self.command_processor.process("iventory")
        self.assertIn("not recognized", result)
        self.assertIn("Did you mean", result)
        self.assertIn("inventory", result)

    def test_garbage_input_returns_no_suggestions(self):
        """Inputs that don't resemble any command skip the 'Did you mean' line."""
        result = self.command_processor.process("xyzqqqq")
        self.assertIn("not recognized", result)
        self.assertNotIn("Did you mean", result)

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

        with patch.object(self.game.progress, 'update', return_value=[achievement1, achievement2]):
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


class TestSimulateGated(TestCommandBase):
    """Step 1.3: minigames are placeholder stubs gated behind
    config.ENABLE_MINIGAMES until Step 4.1 lands real implementations."""

    def test_simulate_cpu_disabled_when_flag_off(self):
        from computerquest import config
        with patch.object(config, 'ENABLE_MINIGAMES', False):
            cmd = SimulateCommand(self.game, ["cpu"])
            result = cmd.execute()
            self.assertIn("not yet available", result.lower())
            self.assertIsNone(self.game.current_minigame)

    def test_simulate_memory_disabled_when_flag_off(self):
        from computerquest import config
        with patch.object(config, 'ENABLE_MINIGAMES', False):
            cmd = SimulateCommand(self.game, ["memory"])
            result = cmd.execute()
            self.assertIn("not yet available", result.lower())
            self.assertIsNone(self.game.current_minigame)

    def test_simulate_cpu_runs_when_flag_on(self):
        from computerquest import config
        # Need knowledge >= 3 for the existing gate inside start_cpu_minigame.
        self.game.player.knowledge['cpu'] = 5
        with patch.object(config, 'ENABLE_MINIGAMES', True):
            cmd = SimulateCommand(self.game, ["cpu"])
            result = cmd.execute()
            self.assertNotIn("not yet available", result.lower())


class TestSaveLoadRemoved(TestCommandBase):
    """Save/load was a placeholder that silently lost data; removed in
    Step 1.2 until a real implementation lands."""

    def setUp(self):
        super().setUp()
        self.command_processor = CommandProcessor(self.game)

    def test_save_command_not_registered(self):
        for verb in ("save", "load", "saves", "listsaves", "deletesave"):
            self.assertNotIn(verb, self.command_processor.commands)

    def test_save_input_returns_unknown(self):
        result = self.command_processor.process("save")
        self.assertIn("not recognized", result)

if __name__ == "__main__":
    unittest.main()
