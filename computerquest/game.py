"""
Game controller for KodeKloud Computer Quest

Main game logic and controller
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from computerquest.commands import CommandProcessor
from computerquest.config import DIRECTION_MAPPING, VIRUS_TYPES
from computerquest.content import component_info, help_text, render_welcome
from computerquest.mechanics.minigames import CPUPipelineMinigame, MemoryHierarchyMinigame
from computerquest.mechanics.progress import ProgressSystem
from computerquest.mechanics.puzzles import MicroPuzzle, PuzzleSession, load_registry
from computerquest.mechanics.visualizer import ComponentVisualizer
from computerquest.utils.helpers import prefix_match
from computerquest.utils.map_renderer import MAP_POSITIONS
from computerquest.world.architecture import ComputerArchitecture

# Re-exported for backward compatibility with existing imports.
__all__ = ["CPUPipelineMinigame", "ComponentVisualizer", "Game", "MemoryHierarchyMinigame"]

# Verbs whose execution does not change persistent game state. Used by feed()
# to decide whether to flip the changes_since_save flag.
_READ_ONLY_VERBS = frozenset({
    "save", "load", "saves", "listsaves", "deletesave",
    "help", "h", "?", "clear", "cls", "c", "quit", "exit", "q",
    "look", "l", "examine", "ex", "map", "m", "motherboard", "mb",
    "status", "progress", "knowledge", "achievements", "stats",
    "inventory", "i", "about", "visualize", "viz",
    # solve/hint/skip/difficulty write puzzle-session state that schemas 1.2
    # and 1.3 persist, so they are NOT read-only: leaving them here meant
    # quitting after them skipped the save prompt and lost the work.
    "objectives", "next",
})


class Game:
    def __init__(self) -> None:
        """
        Constructor: Create a KodeKloud Computer Quest game
        Initialize the game world and components
        """
        # Initialize computer architecture
        self.game_map = ComputerArchitecture()
        self.game_map.setup()

        # Get player from the map
        self.player = self.game_map.player

        # Game state variables
        self.turns = 0
        self.game_over = False
        self.victory = False
        # Save tracking — set by SaveCommand/LoadCommand and read by QuitCommand
        # to offer a save prompt if there are unsaved changes.
        self.last_save_turn = 0
        self.changes_since_save = False

        # Initialize the progress tracking system
        self.progress = ProgressSystem(self)

        # Initialize visualizer
        self.visualizer = ComponentVisualizer()

        # Initialize minigame state
        self.current_minigame: CPUPipelineMinigame | MemoryHierarchyMinigame | None = None
        self.current_visualization: str | None = None

        # Micro-puzzle state lives in PuzzleSession (contract:
        # docs/architecture-microquiz.md); Game delegates to it.
        self.puzzle_registry = load_registry()
        self.puzzles = PuzzleSession(self.puzzle_registry, self.player, self.game_map.rooms)

        # Initialize save/load system
        from computerquest.mechanics.save_load import SaveLoadSystem
        self.save_load = SaveLoadSystem(self)

        # Initialize command processor
        self.command_processor = CommandProcessor(self)

        # The player starts standing in a room, so it counts as visited. This
        # is recorded on the component itself, the single source of truth that
        # both the ASCII map and the web snapshot read.
        self.player.location.mark_visited()

        # Welcome message is shown by start(), not __init__, so the constructor
        # has no I/O side effects and remains testable.

    @property
    def map_grid(self) -> dict[str, dict[str, bool]]:
        """Per-room visit state for the ASCII map renderer.

        A derived view over game_map.rooms rather than stored state: the
        component's own `visited` flag is the single source of truth, so the
        ASCII map and the web snapshot can never disagree, and adding a room
        needs no second registration here.
        """
        return {
            room_id: {"visited": room.visited}
            for room_id, room in self.game_map.rooms.items()
        }

    def setup_readline(self) -> bool:
        """
        Setup readline for command history and tab completion
        """
        try:
            import readline
            import rlcompleter  # noqa: F401  # imported for tab-complete side effects

            # Define our custom completer function for game commands
            def completer(text: str, state: int) -> str | None:
                # First, try to complete commands
                command_options = [
                    cmd for cmd in self.command_processor.commands.keys() if cmd.startswith(text)
                ]

                # Then, try to complete directions
                direction_options = [
                    dir_name
                    for dir_name in self.command_processor.direction_words
                    if dir_name.startswith(text)
                ]

                # Finally, try to complete items in the current location or inventory
                item_options = []
                if self.player and self.player.location:
                    # Items in current location
                    item_options.extend(
                        [
                            item
                            for item in self.player.location.items.keys()
                            if isinstance(item, str) and item.startswith(text)
                        ]
                    )

                if self.player:
                    # Items in inventory
                    item_options.extend(
                        [
                            item
                            for item in self.player.items.keys()
                            if isinstance(item, str) and item.startswith(text)
                        ]
                    )

                # Special cases for specific commands
                words = readline.get_line_buffer().split()
                if len(words) > 0 and words[0] in ["take", "get", "t"]:
                    # Only show items in the room for take command
                    if self.player and self.player.location:
                        item_options = [
                            item
                            for item in self.player.location.items.keys()
                            if isinstance(item, str) and item.startswith(text)
                        ]

                # Combine all options
                options = command_options + direction_options + item_options

                # Return the state-th completion or None if no more completions
                if state < len(options):
                    return options[state]
                return None

            # Set the completer function
            readline.set_completer(completer)

            # Set the word delimiters for completion
            readline.set_completer_delims(" \t\n;")

            # Use tab for completion
            readline.parse_and_bind("tab: complete")

            # Set history file
            import os

            histfile = os.path.join(os.path.expanduser("~"), ".computerquest_history")
            try:
                readline.read_history_file(histfile)
                # Set history length
                readline.set_history_length(100)
            except OSError:
                # File missing, empty, or otherwise unreadable — start fresh
                pass

            # Save history on exit
            import atexit

            atexit.register(readline.write_history_file, histfile)

            return True
        except (ImportError, AttributeError):
            # Readline is not available on all platforms
            print("Note: Command history and tab completion are not available on this system.")
            return False

    @property
    def all_viruses_found(self) -> bool:
        """True once every canonical virus has been detected.

        Derived from the player's found list so it stays correct no matter
        which scan variant (whole-room or targeted) found the last virus.
        """
        return len(self.player.found_viruses) == len(VIRUS_TYPES)

    def feed(self, line: str) -> str:
        """
        Run one command cycle. Returns the response text.

        This is the single entry point both the CLI (via start()) and the
        web server (server.py) use to drive the game. It only depends on
        the input string and the game's internal state — no print()
        side-effects, no input() calls. The dirty-state flag flips here
        when a state-changing verb is run.
        """
        stripped = line.strip()
        if not stripped:
            return ""

        response = self.command_processor.process(stripped)

        # Resolve the verb the same way the command processor did, so an
        # abbreviated read-only command (e.g. 'know' -> 'knowledge') is not
        # mistaken for a state change and does not trigger a save prompt.
        verb = self._match_command_prefix(stripped.split()[0].lower())
        if verb not in _READ_ONLY_VERBS:
            self.changes_since_save = True

        return response

    def snapshot(self) -> dict[str, Any]:
        """
        Return a structured snapshot of game state for external consumers
        (the web map renderer). Stable wire format — additions are safe,
        renames break clients, so don't.

        Note: every room reference in the snapshot uses the same id space
        (the dict key — 'cpu_package', 'core1', etc.), not the component's
        internal `Component.id` (e.g. 'CPU000'). The frontend treats those
        keys as opaque node identifiers.
        """
        # Door destinations are Component instances; each carries the key it
        # is filed under (assign_room_keys), so translating back to the wire
        # id space is an attribute read rather than a reverse-map rebuild.
        rooms = []
        for room_id, room in self.game_map.rooms.items():
            doors = {
                direction: dest.key
                for direction, dest in room.doors.items()
                if getattr(dest, "key", None) is not None
            }
            # Ship the canonical grid placement so the web map draws the same
            # architecture the ASCII map does. Without it the frontend had to
            # invent its own layout and chose an alphabetical circle, which put
            # unrelated rooms adjacent and drew every corridor as a chord.
            row, col = MAP_POSITIONS.get(room_id, (0, 0))
            rooms.append({
                "id": room_id,
                "name": room.name,
                "visited": room.visited,
                "doors": doors,
                "grid": {"row": row, "col": col},
                "item_count": len(room.items),
                "puzzles": {
                    "available": list(room.puzzles),
                    "solved": [p for p in room.puzzles if p in self.player.solved_puzzles],
                    "attempted": [
                        p for p in room.puzzles if p in self.player.attempted_puzzles
                    ],
                },
            })

        player_location_id = self._current_room_id()

        return {
            "turn": self.turns,
            "game_over": self.game_over,
            "victory": self.victory,
            "all_viruses_found": self.all_viruses_found,
            "player": {
                "name": self.player.name,
                "location_id": player_location_id,
                "health": self.player.health,
                "max_health": self.player.max_health,
                "items": list(self.player.items.keys()),
                "knowledge": dict(self.player.knowledge),
            },
            "rooms": rooms,
            "found_viruses": list(self.player.found_viruses),
            "quarantined_viruses": list(self.player.quarantined_viruses),
        }

    def welcome_text(self) -> str:
        """Render the welcome banner to a string instead of stdout."""
        return render_welcome(self.player)

    def start(self) -> None:
        """
        Main CLI game loop. Drives the game via feed() one line at a time
        and renders responses to stdout. The server uses feed() directly
        and skips this loop entirely.
        """
        # Show welcome screen here (moved out of __init__ so construction
        # has no I/O side effects).
        self.display_welcome()

        # Setup readline for command history and tab completion
        has_readline = self.setup_readline()
        if has_readline:
            from computerquest.utils.helpers import Colors

            print(
                f"\n{Colors.GREEN}TIP:{Colors.RESET} Use {Colors.BOLD}Tab{Colors.RESET} for command completion and {Colors.BOLD}Up/Down arrows{Colors.RESET} for command history!"
            )

        # Loop until victory or quit
        while not self.game_over:
            # Get user input
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                # Handle Ctrl+D or Ctrl+C gracefully. If state is dirty,
                # offer to save before exiting. The prompt itself can also
                # be interrupted — in that case treat it as a "no".
                print("\nInterrupted. ")
                if self.changes_since_save:
                    try:
                        if input("Save before exiting? (y/n): ").lower() in ('y', 'yes'):
                            print(self.save_load.save_game())
                    except (EOFError, KeyboardInterrupt):
                        print()
                print("Exiting...")
                self.game_over = True
                break

            response = self.feed(user_input)
            if not response:
                continue

            # Clear the screen before showing the new output. ANSI escapes on
            # a TTY only — keeps piped output (e.g. test capture) clean.
            import sys

            if sys.stdout.isatty():
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()

            # Display result
            print(f"\n{response}")

        # Game over - ask to play again or exit
        if self.victory:
            print("\nWould you like to play again? (y/n)")
            replay = input("> ").lower()
            if replay in ["y", "yes"]:
                # Reset and start new game
                Game.__init__(self)
                self.start()
            else:
                print("\nThank you for playing KodeKloud Computer Quest! Goodbye!")
        else:
            print("\nExiting KodeKloud Computer Quest. Goodbye!")

    def display_welcome(self) -> None:
        """Print the welcome banner. Text itself lives in computerquest.content."""
        print(render_welcome(self.player), end="")

    def move(self, direction: str) -> str:
        """
        Move the player in the specified direction
        direction: Direction to move (n, s, e, w, etc.)
        Returns: Description of new location or error message
        """
        # Normalize direction input
        dir_code = DIRECTION_MAPPING.get(direction, direction)

        # Track previous location to provide feedback
        prev_location = self.player.location

        # Attempt to move
        if self.player.go(dir_code):
            # If successfully moved
            curr_location = self.player.location

            # Mark newly visited components. map_grid derives from this, so
            # there is no second bookkeeping step.
            curr_location.mark_visited()

            # Update turn counter
            self.turns += 1

            # Add system architecture educational note on first visit
            if prev_location.name != curr_location.name:
                # Create movement header with fancy styling
                result = "┏━━━━━━━━━━━━━━━━━━━━ MOVEMENT ━━━━━━━━━━━━━━━━━━━━┓\n"
                result += f"  Moved from {prev_location.name} to {curr_location.name}.\n"
                result += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

                # The arriving description is the same thing `look` renders,
                # so ask the player for it rather than rebuilding it. Both
                # sides used to assemble the technical readout independently,
                # which meant looking at a room and walking into it could drift
                # apart and report different details about the same component.
                result += self.player.look()

                # Handle any NPCs or hostile entities
                if curr_location.play:
                    # In future versions, handle encounters here
                    pass

                # First visit to a puzzle room auto-presents its primary
                # puzzle (decision 4). Never interrupts an active puzzle.
                auto = self._maybe_auto_prompt()
                if auto:
                    result += "\n\n" + auto

                return result
            else:
                # This shouldn't happen with the current implementation
                return f"You remain at {curr_location.name}."
        else:
            # Failed to move
            return f"┏━━━━━━━━━━━━━━━━━━━━ ERROR ━━━━━━━━━━━━━━━━━━━━┓\n  There is no connection to the {direction} from {self.player.location.name}.\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

    # --- Micro-puzzle surface: delegates to PuzzleSession -------------------
    # These wrappers keep Game's public API stable for commands.py, the save
    # system, and existing tests while the state itself lives in the session.

    @property
    def current_puzzle(self) -> MicroPuzzle | None:
        return self.puzzles.current

    @current_puzzle.setter
    def current_puzzle(self, value: MicroPuzzle | None) -> None:
        self.puzzles.current = value

    @property
    def puzzle_hints_used(self) -> int:
        return self.puzzles.hints_used

    @puzzle_hints_used.setter
    def puzzle_hints_used(self, value: int) -> None:
        self.puzzles.hints_used = value

    @property
    def prompted_rooms(self) -> set[str]:
        return self.puzzles.prompted_rooms

    def _current_room_id(self) -> str | None:
        return self.puzzles.current_room_id()

    def _gated_room_puzzles(self) -> list[MicroPuzzle]:
        return self.puzzles.gated_room_puzzles()

    def _maybe_auto_prompt(self) -> str:
        return self.puzzles.maybe_auto_prompt()

    def list_room_puzzles(self) -> str:
        return self.puzzles.list_room_puzzles()

    def start_puzzle(self, puzzle_id: str | None = None) -> str:
        return self.puzzles.start(puzzle_id)

    def answer_puzzle(self, raw: str) -> str:
        return self.puzzles.answer(raw)

    def puzzle_hint(self) -> str:
        return self.puzzles.hint()

    def skip_puzzle(self) -> str:
        return self.puzzles.skip()

    def _recompute_knowledge(self) -> None:
        self.puzzles.recompute_knowledge()

    def display_map(self) -> str:
        """
        Display an interactive map of visited rooms
        Returns: ASCII map showing explored components
        """
        from computerquest.utils.map_renderer import render_map

        # The room the player is standing in is visited by definition; the
        # constructor and move() both record it on the component.
        self.player.location.mark_visited()

        # Generate and return the map
        return render_map(self, self.map_grid)

    def show_help(self) -> str:
        """Show available commands. Text lives in computerquest.content."""
        return help_text()

    def start_cpu_minigame(self) -> str:
        """Start the CPU pipeline simulation minigame"""
        if self.player.knowledge["cpu"] < 3:
            return "You need more knowledge about CPU architecture to understand this simulation. Explore CPU components and learn more first."

        self.current_minigame = CPUPipelineMinigame(self)

        return (
            self.current_minigame.explain()
            + "\n\n"
            + self.current_minigame.get_status()
            + "\n\nUse 'simulate step' to advance the simulation, 'simulate toggle' to switch modes, and 'simulate reset' to restart."
        )

    def start_memory_minigame(self) -> str:
        """Start the memory hierarchy simulation minigame"""
        if self.player.knowledge["memory"] < 3:
            return "You need more knowledge about memory systems to understand this simulation. Explore memory components and learn more first."

        self.current_minigame = MemoryHierarchyMinigame(self)

        return self.current_minigame.explain()

    def handle_visualization(self, viz_type: str | None = None) -> str:
        """Handle visualization commands"""
        if not viz_type or viz_type in ["help", "list", "?"]:
            return """Available visualizations:
- 'viz cpu': CPU architecture visualization
- 'viz memory': Memory hierarchy visualization
- 'viz network': Network protocol stack visualization
- 'viz storage': Storage systems visualization
- 'viz motherboard': Motherboard layout visualization

Usage: viz [type] (e.g., 'viz cpu')"""

        viz_type = viz_type.lower()

        if viz_type in ["cpu", "processor"]:
            self.current_visualization = "cpu"
            # Using default parameters for the CPU visualization
            return (
                "Displaying CPU visualization in text mode:\n\n"
                + self.visualizer.render_cpu_text(clock_speed=3.6, cores=4, cache=8)
            )

        elif viz_type in ["memory", "ram", "cache"]:
            self.current_visualization = "memory"
            return (
                "Displaying memory hierarchy visualization in text mode:\n\n"
                + self.visualizer.render_memory_hierarchy_text()
            )

        elif viz_type in ["network", "protocol"]:
            self.current_visualization = "network"
            return (
                "Displaying network protocol stack visualization in text mode:\n\n"
                + self.visualizer.render_network_stack_text()
            )

        elif viz_type in ["storage", "disk", "drive"]:
            self.current_visualization = "storage"
            return (
                "Displaying storage systems visualization in text mode:\n\n"
                + self.visualizer.render_storage_hierarchy_text()
            )

        elif viz_type in ["motherboard", "mb", "mainboard"]:
            self.current_visualization = "motherboard"
            return (
                "Displaying motherboard layout visualization in text mode:\n\n"
                + self.visualizer.render_motherboard_layout_text()
            )

        elif viz_type == "stop":
            prev_viz = self.current_visualization
            self.current_visualization = None
            return f"Stopped {prev_viz} visualization. Returning to text mode."

        else:
            return f"Unknown visualization type: {viz_type}. Try 'cpu', 'memory', 'network', 'storage', or 'motherboard'."

    def handle_simulation(self, action: str | None = None, params: list[str] | None = None) -> str:
        """Handle simulation commands. `params` carries extra tokens for
        verbs that take an argument (pattern <name>, cache <level> <size>)."""
        if not self.current_minigame:
            return "No active simulation. Start one with 'simulate cpu' or 'simulate memory'."

        if not action:
            return "Please specify a simulation action: 'step', 'toggle', 'reset', or 'stop'."

        params = params or []
        action = action.lower()
        mini = self.current_minigame

        if action == "step":
            return mini.step()

        elif action == "status":
            return mini.get_status()

        elif action == "toggle":
            if hasattr(mini, "toggle_pipeline"):
                return mini.toggle_pipeline()
            return "This simulation doesn't support toggling modes."

        elif action == "forward":
            if hasattr(mini, "toggle_forwarding"):
                return mini.toggle_forwarding()
            return "This simulation doesn't support forwarding."

        elif action == "pattern":
            if not hasattr(mini, "set_pattern"):
                return "This simulation doesn't support access patterns."
            if not params:
                return "Usage: simulate pattern <sequential|loop|stride|random>"
            return mini.set_pattern(params[0].lower())

        elif action == "cache":
            if not hasattr(mini, "set_cache_size"):
                return "This simulation doesn't support cache tuning."
            if len(params) < 2 or not params[1].isdigit():
                return "Usage: simulate cache l1 <size>"
            return mini.set_cache_size(int(params[1]))

        elif action == "reset":
            return mini.reset()

        elif action == "stop":
            self.current_minigame = None
            return "Simulation stopped."

        else:
            return (
                f"Unknown simulation action: {action}. Try 'step', 'status', 'toggle', "
                "'forward', 'pattern', 'cache', 'reset', or 'stop'."
            )

    def get_component_info(self, topic: str) -> str:
        """Educational article for a topic. Text lives in computerquest.content."""
        return component_info(topic)

    def display_motherboard(self) -> str:
        """Display the full motherboard layout of the computer system.

        Single source of truth lives in ComponentVisualizer; both this
        method and `viz motherboard` route through it.
        """
        return self.visualizer.render_motherboard_layout_text()

    def victory_message(self) -> str:
        """Generate victory message when all viruses are quarantined"""
        return """
CONGRATULATIONS! MISSION SUCCESSFUL!

You have successfully located and quarantined all viruses in the system.
The computer architecture is now secure and operating at optimal efficiency.

During your mission, you've explored the inner workings of computer components
and how they interconnect to form a complete system.

Your final statistics:
- Turns taken: {turns}
- Computer components visited: {components}/{total_components}
- Knowledge gained: {knowledge_level}

Thank you for playing KodeKloud Computer Quest!
""".format(
            turns=self.turns,
            components=sum(1 for room in self.game_map.rooms.values() if room.visited),
            total_components=len(self.game_map.rooms),
            knowledge_level=sum(self.player.knowledge.values()),
        )

    def completions(self, line: str) -> list[str]:
        """Candidate completions for a partial input line.

        One source of truth for both surfaces: the CLI readline completer and
        the web terminal both ask here, so the browser cannot drift from the
        real command table or the room's actual contents.
        """
        parts = line.split()
        trailing_space = line.endswith(" ")
        processor = self.command_processor

        # Completing the verb itself.
        if not parts or (len(parts) == 1 and not trailing_space):
            prefix = parts[0].lower() if parts else ""
            pool = list(processor.commands) + list(processor.direction_words)
            return sorted({c for c in pool if c.startswith(prefix)})

        verb = self._match_command_prefix(parts[0].lower())
        prefix = "" if trailing_space else parts[-1].lower()

        # Argument pools are per-verb, mirroring the readline completer's
        # special case: you can only take what is in the room, drop what you
        # carry, and solve what is bound here.
        if verb in {"take", "get", "t"}:
            pool = list(self.player.location.items)
        elif verb in {"drop"}:
            pool = list(self.player.items)
        elif verb in {"solve"}:
            # The gated list, not the raw room list: `solve <id>` deliberately
            # bypasses the difficulty gate, so offering a locked id as a
            # completion handed over progression for one keypress.
            pool = [p.id for p in self._gated_room_puzzles()]
        elif verb in {"quarantine"}:
            pool = list(self.player.found_viruses)
        elif verb in {"about"}:
            from computerquest.content import COMPONENT_TOPICS

            pool = list(COMPONENT_TOPICS)
        elif verb in {"help", "h"}:
            pool = list(processor.commands)
        elif verb in {"go", "move"}:
            pool = list(processor.direction_words)
        else:
            pool = list(self.player.location.items) + list(self.player.items)

        return sorted({c for c in pool if c.startswith(prefix)})

    def _match_prefix(self, prefix: str, candidates: Iterable[str]) -> str:
        """Resolve a prefix against candidates, returning the unique full match.

        Single-letter input is returned unchanged (too ambiguous to match), and
        an ambiguous or absent prefix falls through to prefix_match's own
        return-unchanged behavior.
        """
        if len(prefix) < 2:
            return prefix
        return prefix_match(prefix, list(candidates))

    def _match_command_prefix(self, cmd: str) -> str:
        """Match a command prefix against the valid command names."""
        return self._match_prefix(cmd, self.command_processor.commands.keys())

    def _match_item_prefix(self, item_prefix: str) -> str:
        """Match an item prefix against items in the current room."""
        return self._match_prefix(item_prefix, self.player.location.items.keys())

    def _match_inventory_item_prefix(self, item_prefix: str) -> str:
        """Match an item prefix against items in the player's inventory."""
        return self._match_prefix(item_prefix, self.player.items.keys())
