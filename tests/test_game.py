#!/usr/bin/env python3
"""
Unit tests for the Game class
"""

import unittest
from unittest.mock import patch, MagicMock, call
import io
import sys
from computerquest.game import Game, CPUPipelineMinigame, SaveLoadSystem
from computerquest.models.component import Component
from computerquest.models.player import Player
from computerquest.commands import CommandProcessor
from tests._helpers import build_real_game

class TestGame(unittest.TestCase):
    """Test cases for the Game class.

    Uses a real Game instance (full ComputerArchitecture, real Player, real
    CommandProcessor). Tests that need to control a specific method's return
    value use a narrow patch.object scoped to that method.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.game = build_real_game()
        # Reset turn-counter so individual tests start from a known state
        # (the welcome banner doesn't bump turns, but be explicit).
        self.game.turns = 0
        self.game.game_over = False
        self.game.all_viruses_found = False
        self.game.victory = False
    
    def test_init(self):
        """Test game initialization"""
        game = self.game

        self.assertIsNotNone(game.game_map)
        self.assertIsNotNone(game.player)
        self.assertEqual(game.turns, 0)
        self.assertFalse(game.game_over)
        self.assertFalse(game.all_viruses_found)
        self.assertFalse(game.victory)

        # Subsystems
        self.assertIsNotNone(game.progress)
        self.assertIsNotNone(game.visualizer)
        self.assertIsNone(game.current_minigame)
        self.assertIsNone(game.current_visualization)
        self.assertIsNotNone(game.save_load)
        self.assertIsNotNone(game.command_processor)
        self.assertIsNotNone(game.map_grid)
    
    @patch('builtins.print')
    @patch('builtins.input', return_value="help")
    def test_start(self, mock_input, mock_print):
        """Test the main game loop"""
        # Stub readline setup so the loop doesn't try to load a history file
        # from a path that may not be writable in test environments.
        with patch.object(self.game, 'setup_readline', return_value=False):
            self.game.command_processor = MagicMock()

            def set_game_over(*args, **kwargs):
                self.game.game_over = True
                return "Command executed"
            self.game.command_processor.process.side_effect = set_game_over

            self.game.start()

        mock_input.assert_called_once()
        self.game.command_processor.process.assert_called_once_with("help")
        # The loop prints command output, then prints a goodbye on exit;
        # confirm command output appeared (not just the final goodbye).
        mock_print.assert_any_call("\nCommand executed")
    
    @patch('builtins.print')
    def test_display_welcome(self, mock_print):
        """Test welcome message display"""
        self.game.display_welcome()

        # ANSI color escapes are interleaved with the literal text, so match
        # an unbroken substring that survives the escape boundaries.
        all_output = "\n".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("KodeKloud Computer Architecture Quest", all_output)
        self.assertIn("MISSION BRIEFING", all_output)
    
    def test_move(self):
        """Test player movement"""
        prev_location = Component(name="Previous Location", description="Starting point")
        new_location = Component(name="New Location", description="Destination")
        self.game.player.location = prev_location

        def side_effect_go(direction):
            self.game.player.location = new_location
            return True

        with patch.object(self.game.player, 'go', side_effect=side_effect_go) as mock_go:
            self.game.game_map.rooms = {"new_room": new_location}
            result = self.game.move("north")
            mock_go.assert_called_with("n")
            self.assertEqual(self.game.turns, 1)
            self.assertIn("Moved from Previous Location to New Location", result)
            self.assertIn(new_location.desc, result)

        # Failed move
        with patch.object(self.game.player, 'go', return_value=False):
            result = self.game.move("west")
            self.assertIn("no connection", result.lower())
    
    @patch('computerquest.utils.map_renderer.render_map')
    def test_display_map(self, mock_render_map):
        """Test map display"""
        mock_render_map.return_value = "ASCII Map Output"
        
        # Set current location to a room in map_grid
        for room_id, room in self.game.game_map.rooms.items():
            if room_id in self.game.map_grid:
                self.game.player.location = room
                break
        
        result = self.game.display_map()
        
        # Check map renderer was called
        mock_render_map.assert_called_once()
        self.assertEqual(result, "ASCII Map Output")
    
    def test_show_help(self):
        """Test help display"""
        help_text = self.game.show_help()
        
        # Check help text contains important command categories
        self.assertIn("KODEKLOUD COMPUTER QUEST COMMANDS", help_text)
        self.assertIn("Movement:", help_text)
        self.assertIn("Exploration:", help_text)
        self.assertIn("Inventory:", help_text)
        self.assertIn("Security Functions:", help_text)
    
    def test_start_cpu_minigame(self):
        """Test starting CPU minigame"""
        # Test without required knowledge
        self.game.player.knowledge = {"cpu": 2}  # Below required level
        result = self.game.start_cpu_minigame()
        self.assertIn("need more knowledge", result.lower())
        self.assertIsNone(self.game.current_minigame)
        
        # Test with required knowledge
        self.game.player.knowledge = {"cpu": 5}  # Above required level
        result = self.game.start_cpu_minigame()
        self.assertIsNotNone(self.game.current_minigame)
        self.assertIsInstance(self.game.current_minigame, CPUPipelineMinigame)
        self.assertIn("CPU Pipeline", result)
    
    def test_handle_visualization(self):
        """Test visualization handling"""
        # Without a type, returns the menu of available visualizations.
        result = self.game.handle_visualization()
        self.assertIn("Available visualizations", result)

        # Test CPU visualization
        result = self.game.handle_visualization("cpu")
        self.assertEqual(self.game.current_visualization, "cpu")
        self.assertIn("CPU", result)
        self.assertIn("CPU ARCHITECTURE", result)

        # Test memory visualization
        result = self.game.handle_visualization("memory")
        self.assertEqual(self.game.current_visualization, "memory")
        self.assertIn("MEMORY", result.upper())
        
        # Test stopping visualization
        prev_viz = self.game.current_visualization
        result = self.game.handle_visualization("stop")
        self.assertIsNone(self.game.current_visualization)
        self.assertIn(f"Stopped {prev_viz} visualization", result)
        
        # Test unknown visualization type
        result = self.game.handle_visualization("unknown")
        self.assertIn("Unknown visualization type", result)
    
    def test_handle_simulation(self):
        """Test simulation handling"""
        # Without active simulation
        result = self.game.handle_simulation()
        self.assertIn("No active simulation", result)

        # start_cpu_minigame requires knowledge['cpu'] >= 3; seed it.
        self.game.player.knowledge['cpu'] = 5
        self.game.start_cpu_minigame()

        # Without action specified
        result = self.game.handle_simulation()
        self.assertIn("Please specify a simulation action", result)

        # Step
        result = self.game.handle_simulation("step")
        self.assertIn("Advanced pipeline by one step", result)

        # Toggle
        result = self.game.handle_simulation("toggle")
        self.assertIn("Toggled pipeline mode", result)

        # Reset
        result = self.game.handle_simulation("reset")
        self.assertIn("Reset pipeline simulation", result)

        # Stop
        result = self.game.handle_simulation("stop")
        self.assertIsNone(self.game.current_minigame)
        self.assertIn("Simulation stopped", result)

        # Unknown action
        self.game.start_cpu_minigame()
        result = self.game.handle_simulation("unknown")
        self.assertIn("Unknown simulation action", result)
    
    def test_get_component_info(self):
        """Test educational component information"""
        # Valid topics
        cpu_info = self.game.get_component_info("cpu")
        self.assertIn("CPU (Central Processing Unit)", cpu_info)

        memory_info = self.game.get_component_info("memory")
        self.assertIn("Computer Memory Hierarchy", memory_info)

        # Unknown topic falls through to the suggestions surface.
        unknown_result = self.game.get_component_info("processor")
        self.assertIn("No information available", unknown_result)
        self.assertIn("cpu", unknown_result.lower())

        # Completely unknown topic
        very_unknown = self.game.get_component_info("xyzabc")
        self.assertIn("No information available", very_unknown)
    
    def test_display_motherboard(self):
        """Test motherboard diagram display"""
        result = self.game.display_motherboard()
        
        # Check diagram contains key components
        self.assertIn("KodeKloud Computer Quest Motherboard Layout", result)
        self.assertIn("CPU Package", result)
        self.assertIn("Core 1", result)
        self.assertIn("L3 Cache", result)
        self.assertIn("RAM DIMM", result)
        self.assertIn("PCH", result)
        self.assertIn("Virus Locations", result)
    
    def test_victory_message(self):
        """Test victory message generation"""
        self.game.turns = 42

        # Mark a couple of rooms as visited (dict_values is not subscriptable
        # in Python 3, so materialize first).
        for room in list(self.game.game_map.rooms.values())[:2]:
            room.visited = True

        self.game.player.knowledge = {"cpu": 3, "memory": 2, "storage": 1, "networking": 0, "security": 5}

        result = self.game.victory_message()
        self.assertIn("CONGRATULATIONS", result)
        self.assertIn("Turns taken: 42", result)
        self.assertIn("Thank you for playing", result)
    
    def test_prefix_matching(self):
        """Test helper methods for prefix matching"""
        # Setup test data
        self.game.command_processor.commands = {
            "look": None,
            "load": None,
            "location": None
        }
        
        self.game.player.location.items = {
            "document": "A document",
            "desk": "A desk",
            "door": "A door"
        }
        
        self.game.player.items = {
            "tablet": "A tablet",
            "tool": "A tool"
        }
        
        # Test exact matches
        self.assertEqual(self.game._match_command_prefix("look"), "look")
        self.assertEqual(self.game._match_item_prefix("document"), "document")
        self.assertEqual(self.game._match_inventory_item_prefix("tablet"), "tablet")
        
        # Test unique prefix matches
        self.assertEqual(self.game._match_command_prefix("loo"), "look")
        self.assertEqual(self.game._match_item_prefix("doc"), "document")
        self.assertEqual(self.game._match_inventory_item_prefix("ta"), "tablet")
        
        # Test ambiguous prefix (should return original)
        self.assertEqual(self.game._match_command_prefix("lo"), "lo")  # Ambiguous: look, load, location
        self.assertEqual(self.game._match_item_prefix("d"), "d")       # Ambiguous: document, desk, door
        
        # Test non-matching prefix
        self.assertEqual(self.game._match_command_prefix("xyz"), "xyz")
        self.assertEqual(self.game._match_item_prefix("xyz"), "xyz")
        self.assertEqual(self.game._match_inventory_item_prefix("xyz"), "xyz")

class TestCPUPipelineMinigame(unittest.TestCase):
    """Test cases for the CPU Pipeline Minigame"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game = MagicMock()
        self.minigame = CPUPipelineMinigame(self.game)
    
    def test_explain(self):
        """Test explanation text"""
        result = self.minigame.explain()
        self.assertIn("CPU Pipeline Minigame", result)
    
    def test_get_status(self):
        """Test status display"""
        result = self.minigame.get_status()
        self.assertIn("CPU Pipeline status", result)
    
    def test_step(self):
        """Test stepping the simulation"""
        result = self.minigame.step()
        self.assertIn("Advanced pipeline by one step", result)
    
    def test_toggle_pipeline(self):
        """Test toggling pipeline mode"""
        result = self.minigame.toggle_pipeline()
        self.assertIn("Toggled pipeline mode", result)
    
    def test_reset(self):
        """Test resetting the simulation"""
        result = self.minigame.reset()
        self.assertIn("Reset pipeline simulation", result)

class TestSaveLoadSystem(unittest.TestCase):
    """Test cases for the SaveLoadSystem"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game = MagicMock()
        self.save_system = SaveLoadSystem(self.game)
    
    def test_save_game(self):
        """Test saving game"""
        # Test with default name
        result = self.save_system.save_game()
        self.assertIn("Game saved with name: autosave", result)
        
        # Test with custom name
        result = self.save_system.save_game("custom_save")
        self.assertIn("Game saved with name: custom_save", result)
    
    def test_load_game(self):
        """Test loading game"""
        result = self.save_system.load_game("test_save")
        self.assertIn("Game loaded: test_save", result)
    
    def test_list_saves(self):
        """Test listing saved games"""
        result = self.save_system.list_saves()
        self.assertIn("Available saved games", result)
    
    def test_delete_save(self):
        """Test deleting a saved game"""
        result = self.save_system.delete_save("test_save")
        self.assertIn("Deleted save: test_save", result)

if __name__ == "__main__":
    unittest.main()