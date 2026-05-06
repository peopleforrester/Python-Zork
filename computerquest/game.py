"""
Game controller for KodeKloud Computer Quest

Main game logic and controller
"""

from __future__ import annotations

from computerquest.commands import CommandProcessor
from computerquest.config import DIRECTION_MAPPING
from computerquest.mechanics.minigames import CPUPipelineMinigame, MemoryHierarchyMinigame
from computerquest.mechanics.progress import ProgressSystem
from computerquest.mechanics.visualizer import ComponentVisualizer
from computerquest.utils.helpers import prefix_match
from computerquest.world.architecture import ComputerArchitecture

# Re-exported for backward compatibility with existing imports.
__all__ = ["CPUPipelineMinigame", "ComponentVisualizer", "Game", "MemoryHierarchyMinigame"]


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
        self.all_viruses_found = False
        self.victory = False
        # Initialize the progress tracking system
        self.progress = ProgressSystem(self)

        # Initialize visualizer
        self.visualizer = ComponentVisualizer()

        # Initialize minigame state
        self.current_minigame = None
        self.current_visualization = None

        # Initialize command processor
        self.command_processor = CommandProcessor(self)

        # Initialize map grid for tracking visited rooms
        self._init_map_grid()

        # Mark the starting room as visited on the map
        for room_id, room in self.game_map.rooms.items():
            if room == self.player.location:
                if room_id in self.map_grid:
                    self.map_grid[room_id]["visited"] = True
                break

        # Print welcome message
        self.display_welcome()

    def _init_map_grid(self) -> None:
        """Initialize the map grid for tracking visited components"""
        self.map_grid = {}

        # CPU and cores
        cpu_components = [
            "cpu_package",
            "core1",
            "core1_cu",
            "core1_alu",
            "core1_registers",
            "core1_l1",
            "core2",
            "core2_cu",
            "core2_alu",
            "core2_registers",
            "core2_l1",
        ]

        # Cache and memory
        memory_components = [
            "l2_cache1",
            "l2_cache2",
            "l3_cache",
            "memory_controller",
            "ram_dimm1",
            "ram_dimm2",
            "ram_dimm3",
            "ram_dimm4",
        ]

        # Conceptual components
        conceptual_components = ["kernel", "virtual_memory"]

        # PCH components
        pch_components = [
            "pch",
            "storage_controller",
            "pcie_controller",
            "network_interface",
            "bios",
        ]

        # Storage components
        storage_components = ["sata_ports", "ssd", "hdd"]

        # PCIe components
        pcie_components = ["pcie_x16", "pcie_x1_1", "pcie_x1_2", "gpu"]

        # External ports
        port_components = ["usb_ports", "ethernet"]

        # Combine all components
        all_components = (
            cpu_components
            + memory_components
            + conceptual_components
            + pch_components
            + storage_components
            + pcie_components
            + port_components
        )

        # Initialize all as not visited
        for component in all_components:
            self.map_grid[component] = {"visited": False}

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
            except FileNotFoundError:
                pass

            # Save history on exit
            import atexit

            atexit.register(readline.write_history_file, histfile)

            return True
        except (ImportError, AttributeError):
            # Readline is not available on all platforms
            print("Note: Command history and tab completion are not available on this system.")
            return False

    def start(self) -> None:
        """
        Main game loop
        """
        # Note: No longer clearing the screen at startup
        # The welcome screen is displayed in __init__

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
                # Handle Ctrl+D or Ctrl+C gracefully
                print("\nInterrupted. ")
                print("Exiting...")
                self.game_over = True
                break

            # Skip empty inputs
            if not user_input:
                continue

            # Process command through the command processor
            response = self.command_processor.process(user_input)

            # Clear the screen before showing the new output (except for the first command)
            import os

            os.system("cls" if os.name == "nt" else "clear")

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
        """Display welcome message and game introduction"""
        from computerquest.utils.helpers import Colors

        # Title banner
        print("━" * 78)
        print(
            f"{Colors.CYAN}   █▄▀ █▀█ █▀▄ █▀▀ █▄▀ █   █▀█ █░█ █▀▄   █▀▀ █▀█ █▀▄▀█ █▀█ █░█ ▀█▀ █▀▀ █▀█   █▀█ █░█ █▀▀ █▀ ▀█▀{Colors.RESET}"
        )
        print(
            f"{Colors.CYAN}   █░█ █▄█ █▄▀ ██▄ █░█ █▄▄ █▄█ █▄█ █▄▀   █▄▄ █▄█ █░▀░█ █▀▀ █▄█ ░█░ ██▄ █▀▄   ▀▀█ █▄█ ██▄ ▄█ ░█░{Colors.RESET}"
        )
        print("━" * 78)

        # Consolidated mission briefing
        print(
            f"\n┏━━━━━━━━━━━━━━━━━━━━━━━━ {Colors.YELLOW}{Colors.BOLD}MISSION BRIEFING{Colors.RESET} ━━━━━━━━━━━━━━━━━━━━━━━━┓"
        )
        print("│                                                                    │")
        print(
            f"│  Welcome to the {Colors.CYAN}KodeKloud Computer Architecture Quest!{Colors.RESET}             │"
        )
        print("│                                                                    │")
        print("│  You are a security program deployed into a computer system        │")
        print(
            f"│  infected with multiple {Colors.RED}viruses{Colors.RESET}. Your mission is to locate and     │"
        )
        print("│  quarantine all viruses while learning about computer architecture.│")
        print("│                                                                    │")
        print("│  As you travel through the system, from CPU to memory to storage   │")
        print("│  and beyond, you'll discover how each component works and how      │")
        print("│  they interconnect.                                                │")
        print("│                                                                    │")
        print("│  Good luck, Security Program! The system's integrity depends on you│")
        print("│                                                                    │")
        print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

        # Welcome status bar reads from the real player so values stay in
        # sync with mid-game state if display_welcome is ever re-invoked.
        from computerquest.config import INVENTORY_LIMIT, VIRUS_TYPES
        total_viruses = len(VIRUS_TYPES)
        max_health = self.player.max_health
        current_health = self.player.health
        items_carried = len(self.player.items)
        found = len(self.player.found_viruses)
        quarantined = len(self.player.quarantined_viruses)

        print("\n" + "━" * 78)
        print(
            f"  {Colors.BOLD}STATUS:{Colors.RESET} Health: {Colors.GREEN}{current_health}/{max_health}{Colors.RESET} | Items: {items_carried}/{INVENTORY_LIMIT} | Viruses: {Colors.GREEN}{found}/{total_viruses} Found, {quarantined}/{total_viruses} Quarantined{Colors.RESET}"
        )
        print("━" * 78)

        # Help command reference - streamlined
        print(
            f"\n  {Colors.BOLD}CONTROLS:{Colors.RESET} Type '{Colors.GREEN}?{Colors.RESET}' for command help | '{Colors.GREEN}n/s/e/w{Colors.RESET}' to move | '{Colors.GREEN}l{Colors.RESET}' to look | '{Colors.GREEN}i{Colors.RESET}' for inventory"
        )

        # Show initial location using new format - KEEPING THIS AS THE MAIN FOCUS
        from computerquest.utils.helpers import format_look_output

        print(
            f"\n{format_look_output(self.player.location, self.player.location.doors, list(self.player.location.items.keys()), player=self.player)}"
        )

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

            # Mark newly visited components
            curr_location.mark_visited()

            # Update map - find which room this is
            for room_id, room in self.game_map.rooms.items():
                if room == curr_location:
                    # Found the room ID
                    if room_id in self.map_grid:
                        self.map_grid[room_id]["visited"] = True
                    break

            # Update turn counter
            self.turns += 1

            # Add system architecture educational note on first visit
            if prev_location.name != curr_location.name:
                # Create movement header with fancy styling
                result = "┏━━━━━━━━━━━━━━━━━━━━ MOVEMENT ━━━━━━━━━━━━━━━━━━━━┓\n"
                result += f"  Moved from {prev_location.name} to {curr_location.name}.\n"
                result += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

                # Use the new formatted look output for the current location
                from computerquest.utils.helpers import format_look_output

                # Generate technical details if the component has been visited
                technical_details = None
                if curr_location.visited:
                    technical_details = []
                    if curr_location.security_level > 0:
                        technical_details.append(f"Security Level: {curr_location.security_level}")
                    if curr_location.data_types:
                        technical_details.append(
                            f"Data Types: {', '.join(curr_location.data_types)}"
                        )
                    if any(curr_location.performance.values()):
                        technical_details.append("Performance Metrics:")
                        for metric, value in curr_location.performance.items():
                            if value > 0:
                                technical_details.append(f"  * {metric.capitalize()}: {value}/10")

                result += format_look_output(
                    location=curr_location,
                    connections=curr_location.doors,
                    items=list(curr_location.items.keys()),
                    technical_details=technical_details,
                    player=self.player,
                )

                # Handle any NPCs or hostile entities
                if curr_location.play:
                    # In future versions, handle encounters here
                    pass

                return result
            else:
                # This shouldn't happen with the current implementation
                return f"You remain at {curr_location.name}."
        else:
            # Failed to move
            return f"┏━━━━━━━━━━━━━━━━━━━━ ERROR ━━━━━━━━━━━━━━━━━━━━┓\n  There is no connection to the {direction} from {self.player.location.name}.\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

    def display_map(self) -> str:
        """
        Display an interactive map of visited rooms
        Returns: ASCII map showing explored components
        """
        from computerquest.utils.map_renderer import render_map

        # Make sure starting room is always marked as visited
        for room_id, room in self.game_map.rooms.items():
            if room == self.player.location:
                if room_id in self.map_grid:
                    self.map_grid[room_id]["visited"] = True
                break

        # Generate and return the map
        return render_map(self, self.map_grid)

    def show_help(self) -> str:
        """Show available commands"""
        from computerquest.utils.helpers import Colors

        help_text = f"""┏━━━━━━━━━━━━━━━━━━ {Colors.YELLOW}{Colors.BOLD}KODEKLOUD COMPUTER QUEST COMMANDS{Colors.RESET} ━━━━━━━━━━━━━━━━━━┓
│                                                                          │
│  {Colors.BOLD}Movement:{Colors.RESET}                                                               │
│    go [direction]   - Move between components (n, s, e, w, ne, sw, etc.) │
│    [direction]      - You can also just type the direction (n, s, e, w)  │
│                                                                          │
│  {Colors.BOLD}Exploration:{Colors.RESET}                                                            │
│    {Colors.GREEN}look, l{Colors.RESET}          - Examine your current location                      │
│    {Colors.GREEN}look [item]{Colors.RESET}      - Examine a specific item                            │
│    {Colors.GREEN}read [item], r{Colors.RESET}   - Read text content of an item                       │
│    {Colors.GREEN}map, m{Colors.RESET}           - Display a map of visited computer components       │
│    {Colors.GREEN}motherboard, mb{Colors.RESET}  - Show the motherboard layout of the computer system │
│                                                                          │
│  {Colors.BOLD}Inventory:{Colors.RESET}                                                              │
│    {Colors.GREEN}inventory, i{Colors.RESET}     - List items in your storage                         │
│    {Colors.GREEN}take [item], t{Colors.RESET}   - Add an item to your inventory                      │
│    {Colors.GREEN}drop [item]{Colors.RESET}      - Remove an item from your inventory                 │
│                                                                          │
│  {Colors.BOLD}Security Functions:{Colors.RESET}                                                     │
│    {Colors.GREEN}scan, sc{Colors.RESET}         - Search for viruses in current location             │
│    {Colors.GREEN}scan [item]{Colors.RESET}      - Check if a specific item contains a virus          │
│    {Colors.GREEN}advscan{Colors.RESET}          - Perform advanced scan (requires decoder_tool)      │
│    {Colors.GREEN}advscan [item]{Colors.RESET}   - Perform advanced scan on specific item             │
│    {Colors.GREEN}analyze [item]{Colors.RESET}   - Deeply analyze an item for hidden properties       │
│    {Colors.GREEN}quarantine [virus]{Colors.RESET} - Contain a discovered virus                       │
│                                                                          │
│  {Colors.BOLD}Information:{Colors.RESET}                                                            │
│    {Colors.GREEN}status{Colors.RESET}           - Check your virus discovery progress                │
│    {Colors.GREEN}knowledge{Colors.RESET}        - View your computer architecture knowledge          │
│    {Colors.GREEN}about [topic]{Colors.RESET}    - Get information about a computer component         │
│                                                                          │
│  {Colors.BOLD}Progress Tracking:{Colors.RESET}                                                      │
│    {Colors.GREEN}achievements{Colors.RESET}     - View your achievements and progress report         │
│    {Colors.GREEN}stats{Colors.RESET}            - Alternative command for achievements               │
│                                                                          │
│  {Colors.BOLD}Educational Features:{Colors.RESET}                                                   │
│    {Colors.GREEN}visualize [comp]{Colors.RESET} - Show visualization of a component                  │
│    {Colors.GREEN}viz [comp]{Colors.RESET}       - Shorthand for visualize                            │
│    {Colors.GREEN}simulate cpu{Colors.RESET}     - Start CPU pipeline simulation minigame             │
│    {Colors.GREEN}simulate memory{Colors.RESET}  - Start memory hierarchy simulation                  │
│    {Colors.GREEN}simulate step{Colors.RESET}    - Advance simulation by one step                     │
│    {Colors.GREEN}simulate toggle{Colors.RESET}  - Toggle between simulation modes                    │
│    {Colors.GREEN}simulate reset{Colors.RESET}   - Reset the simulation                               │
│                                                                          │
│  {Colors.BOLD}System:{Colors.RESET}                                                                 │
│    {Colors.GREEN}help, h{Colors.RESET}          - Show this help message                             │
│    {Colors.GREEN}?{Colors.RESET}                - Show quick help overlay                            │
│    {Colors.GREEN}clear, cls, c{Colors.RESET}    - Clear the screen and refresh display               │
│    {Colors.GREEN}quit, q, exit{Colors.RESET}    - Exit the game                                      │
│                                                                          │
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

{Colors.BOLD}Main Shortcuts:{Colors.RESET}
  Movement: {Colors.GREEN}[N]{Colors.RESET}orth {Colors.GREEN}[S]{Colors.RESET}outh {Colors.GREEN}[E]{Colors.RESET}ast {Colors.GREEN}[W]{Colors.RESET}est {Colors.GREEN}[NE]{Colors.RESET} {Colors.GREEN}[SE]{Colors.RESET} {Colors.GREEN}[SW]{Colors.RESET} {Colors.GREEN}[NW]{Colors.RESET} {Colors.CYAN}[U]{Colors.RESET}p {Colors.CYAN}[D]{Colors.RESET}own
  Commands: {Colors.GREEN}[L]{Colors.RESET}ook {Colors.GREEN}[I]{Colors.RESET}nventory {Colors.GREEN}[T]{Colors.RESET}ake {Colors.GREEN}[H]{Colors.RESET}elp {Colors.GREEN}[M]{Colors.RESET}ap {Colors.GREEN}[C]{Colors.RESET}lear {Colors.GREEN}[Q]{Colors.RESET}uit {Colors.GREEN}[Sc]{Colors.RESET}an

Use '{Colors.GREEN}?{Colors.RESET}' for a quick command reference at any time.
"""
        return help_text

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

    def handle_simulation(self, action: str | None = None) -> str:
        """Handle simulation commands"""
        if not self.current_minigame:
            return "No active simulation. Start one with 'simulate cpu' or 'simulate memory'."

        if not action:
            return "Please specify a simulation action: 'step', 'toggle', 'reset', or 'stop'."

        action = action.lower()

        if action == "step":
            return self.current_minigame.step()

        elif action == "toggle":
            if hasattr(self.current_minigame, "toggle_pipeline"):
                return self.current_minigame.toggle_pipeline()
            else:
                return "This simulation doesn't support toggling modes."

        elif action == "reset":
            return self.current_minigame.reset()

        elif action == "stop":
            self.current_minigame = None
            return "Simulation stopped."

        else:
            return f"Unknown simulation action: {action}. Try 'step', 'toggle', 'reset', or 'stop'."

    def get_component_info(self, topic: str) -> str:
        """Provide educational information about computer components"""
        topics = {
            "cpu": """CPU (Central Processing Unit):
The CPU is the primary component that executes instructions and processes data. It consists of:
- Control Unit: Coordinates CPU operations and decodes instructions
- ALU (Arithmetic Logic Unit): Performs mathematical calculations
- Registers: Ultra-fast storage locations for immediate data
- Cache: Fast memory that stores frequently used data
The CPU operates using a cycle of fetch, decode, execute, and writeback phases.""",
            "memory": """Computer Memory Hierarchy:
Computer systems use multiple types of memory arranged in a hierarchy:
1. Registers: Tiny, ultra-fast storage inside the CPU
2. Cache Memory: Small, very fast memory close to the CPU (L1, L2, L3)
3. RAM: Main system memory, volatile (erased when powered off)
4. Virtual Memory: Uses hard drive space as an extension of RAM
5. Storage: HDD/SSD for permanent data storage
As you move down the hierarchy, capacity increases but speed decreases.""",
            "cache": """Cache Memory:
Cache memory serves as a high-speed buffer between the CPU and main memory.
- L1 Cache: Smallest, fastest cache, located in the CPU
- L2 Cache: Larger but slightly slower than L1
- L3 Cache: Largest but slowest cache, often shared between CPU cores
Caches use principles of temporal locality (recently used data will be used again soon) and spatial locality (data near recently used data will be used soon).""",
            "storage": """Storage Systems:
Storage provides permanent data retention, unlike volatile RAM:
- SSD (Solid State Drive): Uses flash memory, no moving parts, fast
- HDD (Hard Disk Drive): Uses magnetic storage on spinning platters
- Storage Controller: Manages data flow between system and storage
- File Systems: Organize data into files and directories
Storage operations are much slower than memory but retain data without power.""",
            "bus": """System Bus Architecture:
Buses are communication pathways that transfer data between components:
- System Bus: Main pathway connecting CPU, memory, and I/O
- Address Bus: Carries memory addresses
- Data Bus: Carries the actual data being transferred
- Control Bus: Carries command signals
- PCI/PCIe: High-speed buses for connecting expansion cards
Bus width (16, 32, 64-bit) determines how much data can be transferred at once.""",
            "network": """Network Interface:
The network component connects the computer to other systems:
- Network Interface Card: Hardware that enables network connectivity
- Protocol Stack: Software layers that format and process network data
- Packets: Units of data transferred over networks
- Protocols: Rules that govern how data is transmitted (e.g., TCP/IP)
Network interfaces handle encoding/decoding data and managing connections.""",
            "firmware": """Firmware/BIOS:
Firmware is software permanently programmed into hardware:
- BIOS/UEFI: Initialize hardware components during boot
- ROM (Read-Only Memory): Stores permanent firmware
- Boot Sequence: Process of starting up computer hardware
- Hardware Configuration: Settings for system components
Firmware operates at a lower level than the operating system.""",
            "gpu": """Graphics Processing Unit (GPU):
The GPU specializes in parallel processing for graphics and computation:
- Shader Cores: Small processors that handle graphical calculations
- VRAM: Specialized memory for storing graphical data
- Render Pipeline: Stages for transforming 3D data to 2D images
- GPGPU: General-purpose computing on GPUs for non-graphics tasks
GPUs excel at tasks that can be broken into many parallel operations.""",
            "kernel": """Operating System Kernel:
The kernel is the core of the operating system:
- Process Management: Creates and schedules processes
- Memory Management: Allocates and tracks system memory
- Device Drivers: Interfaces with hardware components
- File Systems: Manages data storage and retrieval
- System Calls: Provides services to applications
The kernel operates in a privileged mode with direct hardware access.""",
            "virus": """Computer Viruses:
Viruses are malicious programs that can damage systems:
- Boot Sector Virus: Infects system startup areas
- Rootkit: Hides in the operating system kernel
- Memory-Resident Virus: Operates entirely in RAM
- Firmware Virus: Infects system firmware/BIOS
- Network Virus: Spreads via network connections
Viruses typically attempt to hide their presence and propagate to other systems.""",
        }

        if topic in topics:
            return topics[topic]
        else:
            related_topics = []
            for key in topics:
                if key in topic or topic in key:
                    related_topics.append(key)

            if related_topics:
                return f"Topic '{topic}' not found. Did you mean: {', '.join(related_topics)}?"
            else:
                return f"No information available about '{topic}'. Try topics like: cpu, memory, cache, storage, bus, network, firmware, gpu, kernel, or virus."

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

    def _match_command_prefix(self, cmd: str) -> str:
        """Match command prefix with valid commands, return full command if unique match found"""
        if len(cmd) < 2:
            return cmd  # Don't try to match single-letter commands

        # Get all command keys from the command processor
        valid_commands = list(self.command_processor.commands.keys())

        # Use the helper function
        return prefix_match(cmd, valid_commands)

    def _match_item_prefix(self, item_prefix: str) -> str:
        """Match item prefix with items in current room, return full item name if unique match found"""
        if len(item_prefix) < 2:
            return item_prefix  # Don't try to match single-letter items

        # Get all items in current room
        room_items = list(self.player.location.items.keys())

        # Use the helper function
        return prefix_match(item_prefix, room_items)

    def _match_inventory_item_prefix(self, item_prefix: str) -> str:
        """Match item prefix with items in inventory, return full item name if unique match found"""
        if len(item_prefix) < 2:
            return item_prefix  # Don't try to match single-letter items

        # Get all items in inventory
        inventory_items = list(self.player.items.keys())

        # Use the helper function
        return prefix_match(item_prefix, inventory_items)
