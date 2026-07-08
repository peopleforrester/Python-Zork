#!/usr/bin/env python3
"""
Unit tests for the Game class
"""

import unittest
from unittest.mock import MagicMock, patch

from computerquest.game import CPUPipelineMinigame
from computerquest.models.component import Component
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
        self.assertIn("PIPELINE", result.upper())

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

        # Step advances the cycle counter and renders the pipeline.
        result = self.game.handle_simulation("step")
        self.assertIn("Cycle", result)

        # Toggle flips to non-pipelined and restarts.
        result = self.game.handle_simulation("toggle")
        self.assertIn("non-pipelined", result.lower())

        # Reset keeps the mode and returns to cycle 0.
        result = self.game.handle_simulation("reset")
        self.assertIn("Reset", result)

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
    """Smoke tests for the simulator-backed CPU minigame. Full mechanics
    coverage lives in tests/test_minigames.py."""

    def setUp(self):
        """Set up test fixtures"""
        self.game = MagicMock()
        self.minigame = CPUPipelineMinigame(self.game)

    def test_explain(self):
        """Explanation lists the pipeline stages and the workload."""
        result = self.minigame.explain()
        self.assertIn("PIPELINE", result.upper())
        self.assertIn("IF", result)

    def test_get_status(self):
        """Status renders the current cycle without advancing it."""
        result = self.minigame.get_status()
        self.assertIn("Cycle", result)
        self.assertEqual(self.minigame.cycle, 0)

    def test_step(self):
        """Stepping advances the cycle counter."""
        self.minigame.step()
        self.assertEqual(self.minigame.cycle, 1)

    def test_toggle_pipeline(self):
        """Toggling flips to non-pipelined mode and restarts."""
        result = self.minigame.toggle_pipeline()
        self.assertFalse(self.minigame.pipelined)
        self.assertIn("non-pipelined", result.lower())

    def test_reset(self):
        """Reset returns to cycle 0."""
        self.minigame.step()
        result = self.minigame.reset()
        self.assertEqual(self.minigame.cycle, 0)
        self.assertIn("Reset", result)


class TestGameFeed(unittest.TestCase):
    """Game.feed is the single I/O-free entry point used by both the CLI loop
    and the web server (Step 4.2)."""

    def setUp(self) -> None:
        self.game = build_real_game()

    def test_empty_input_returns_empty_and_does_not_dirty(self) -> None:
        self.assertEqual(self.game.feed(""), "")
        self.assertEqual(self.game.feed("   "), "")
        self.assertFalse(self.game.changes_since_save)

    def test_read_only_command_does_not_dirty(self) -> None:
        result = self.game.feed("look")
        self.assertNotEqual(result, "")
        self.assertFalse(self.game.changes_since_save)

    def test_state_changing_command_sets_dirty(self) -> None:
        # 'take' is not in _READ_ONLY_VERBS.
        self.game.feed("take instruction_manual")
        self.assertTrue(self.game.changes_since_save)

    def test_feed_returns_command_processor_output(self) -> None:
        # 'inventory' is read-only but produces predictable output.
        result = self.game.feed("inventory")
        self.assertIn("SYSTEM STORAGE", result)


class TestGameSnapshot(unittest.TestCase):
    """Game.snapshot returns the structured wire format the web map consumes."""

    def setUp(self) -> None:
        self.game = build_real_game()
        self.snap = self.game.snapshot()

    def test_top_level_keys(self) -> None:
        for key in ("turn", "game_over", "victory", "all_viruses_found",
                    "player", "rooms", "found_viruses", "quarantined_viruses"):
            self.assertIn(key, self.snap)

    def test_player_block_shape(self) -> None:
        player = self.snap["player"]
        for key in ("name", "location_id", "health", "max_health",
                    "items", "knowledge"):
            self.assertIn(key, player)
        self.assertEqual(player["health"], self.game.player.health)
        self.assertEqual(player["max_health"], self.game.player.max_health)

    def test_player_location_id_resolves_to_a_real_room(self) -> None:
        location_id = self.snap["player"]["location_id"]
        self.assertIsNotNone(location_id)
        self.assertIn(location_id, self.game.game_map.rooms)

    def test_rooms_block_covers_full_map(self) -> None:
        self.assertEqual(len(self.snap["rooms"]), len(self.game.game_map.rooms))
        seen_ids = {room["id"] for room in self.snap["rooms"]}
        self.assertSetEqual(seen_ids, set(self.game.game_map.rooms.keys()))

    def test_room_doors_use_the_same_id_space_as_rooms_list(self) -> None:
        room_ids = {r["id"] for r in self.snap["rooms"]}
        for room in self.snap["rooms"]:
            for direction, dest_id in room["doors"].items():
                self.assertIn(
                    dest_id, room_ids,
                    f"room {room['id']!r} door {direction!r} -> {dest_id!r} not in rooms list",
                )

    def test_rooms_carry_puzzle_state_blocks(self) -> None:
        """Microquiz step 3: every room exposes available/solved/attempted."""
        core1_l1 = next(r for r in self.snap["rooms"] if r["id"] == "core1_l1")
        self.assertEqual(
            core1_l1["puzzles"]["available"],
            ["l1_lru_basic", "l1_associativity_2way"],
        )
        self.assertEqual(core1_l1["puzzles"]["solved"], [])

        self.game.player.solved_puzzles.add("l1_lru_basic")
        self.game.player.attempted_puzzles.add("l1_lru_basic")
        fresh = self.game.snapshot()
        core1_l1 = next(r for r in fresh["rooms"] if r["id"] == "core1_l1")
        self.assertEqual(core1_l1["puzzles"]["solved"], ["l1_lru_basic"])
        self.assertEqual(core1_l1["puzzles"]["attempted"], ["l1_lru_basic"])

    def test_snapshot_reflects_state_after_feed(self) -> None:
        before = self.game.snapshot()
        self.game.feed("look")  # turn does not advance for look
        after = self.game.snapshot()
        # The player's location should still be valid post-look.
        self.assertEqual(before["player"]["location_id"], after["player"]["location_id"])


class TestGameWelcomeText(unittest.TestCase):
    """Game.welcome_text captures display_welcome's output for non-CLI surfaces."""

    def test_welcome_text_returns_non_empty_string(self) -> None:
        game = build_real_game()
        text = game.welcome_text()
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 100)
        self.assertIn("KodeKloud", text)


if __name__ == "__main__":
    unittest.main()
