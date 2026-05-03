"""
Map renderer module

Handles the rendering of ASCII maps for the game.
"""


def render_map(game, map_grid):
    """
    Render an ASCII map of the computer architecture
    showing only visited components

    Args:
        game: Game instance
        map_grid: Dictionary with visited components

    Returns:
        str: ASCII map representation
    """
    # Template for creating fog of war (unexplored areas)
    empty_frame = [
        "+------------------------------------------------------------------+",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "|                                                                  |",
        "+------------------------------------------------------------------+",
    ]

    # Component parts of the motherboard - will be revealed when visited
    component_parts = {
        "kernel": [
            "|   +----------+                                                 |",
            "|   |          |                                                 |",
            "|   | OS Kernel|                                                 |",
            "|   | (In RAM) |                                                 |",
            "|   +----------+                                                 |",
        ],
        "virtual_memory": [
            "|   +----------+                                                 |",
            "|   | Virtual  |                                                 |",
            "|   | Memory   |                                                 |",
            "|   |          |                                                 |",
            "|   +----------+                                                 |",
        ],
        "cpu_package": [
            "|                    +----------------------------------+         |",
            "|                    |                                  |         |",
            "|                    |           CPU Package            |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    +----------------------------------+         |",
        ],
        "core1": [
            "|                    |  +--------+                      |         |",
            "|                    |  | Core 1 |                      |         |",
            "|                    |  +--------+                      |         |",
        ],
        "core2": [
            "|                    |                    +--------+    |         |",
            "|                    |                    | Core 2 |    |         |",
            "|                    |                    +--------+    |         |",
        ],
        "core_components": [
            "|                    |  | CU|ALU |        | CU|ALU |    |         |",
            "|                    |  | Reg|L1 |        | Reg|L1 |    |         |",
        ],
        "l2_cache": [
            "|                    |  +--------+        +--------+    |         |",
            "|                    |  |L2 Cache|        |L2 Cache|    |         |",
            "|                    |  +--------+        +--------+    |         |",
        ],
        "l3_cache": [
            "|                    |  +----------------------------+   |         |",
            "|                    |  |      L3 Cache (Shared)     |   |         |",
            "|                    |  +----------------------------+   |         |",
        ],
        "ram_dimm1": [
            "|   +----------+                                                 |",
            "|   |RAM DIMM 1|--                                              |",
            "|   +----------+                                                 |",
        ],
        "ram_dimm2": [
            "|   +----------+                                                 |",
            "|   |RAM DIMM 2|                                                 |",
            "|   +----------+                                                 |",
        ],
        "ram_dimm3": [
            "|   +----------+                                                 |",
            "|   |RAM DIMM 3|                                                 |",
            "|   +----------+                                                 |",
        ],
        "ram_dimm4": [
            "|   +----------+                                                 |",
            "|   |RAM DIMM 4|                                                 |",
            "|   +----------+                                                 |",
        ],
        "dmi_link": [
            "|                                    |                           |",
            "|                               DMI Link                         |",
            "|                                    |                           |",
        ],
        "pch": [
            "|                    +----------------------------------+         |",
            "|                    |               PCH                |         |",
            "|                    |     (Platform Controller Hub)    |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    |                                  |         |",
            "|                    +----------------------------------+         |",
        ],
        "pch_controllers": [
            "|                    |  +----------+      +----------+   |         |",
            "|                    |  | Storage  |      |   PCIe   |   |         |",
            "|                    |  |Controller|      |Controller|   |         |",
            "|                    |  +----------+      +----------+   |         |",
        ],
        "pch_components": [
            "|                    |  +----------+      +----------+   |         |",
            "|                    |  | Network  |      |BIOS/UEFI |   |         |",
            "|                    |  |Interface |      |  Flash   |   |         |",
            "|                    |  +----------+      +----------+   |         |",
        ],
        "storage": [
            "|   +------+                                                    |",
            "|   | SSD  |-------                                             |",
            "|   +------+                                                    |",
            "|                                                               |",
            "|   +------+                                                    |",
            "|   | HDD  |---+                                                |",
            "|   +------+   |                                                |",
        ],
        "io_ports": [
            "|                    +-----------------+---------+--------+      |",
            "|                    |  SATA Ports     |    USB Ports    Ethernet |",
            "|                    +-----------------+---------+--------+      |",
        ],
        "pcie_slots": [
            "|                    +----------------+                          |",
            "|                    |  PCIe x16 Slot |                          |",
            "|                    +----------------+                          |",
            "|                                                                |",
            "|                    +----------------+                          |",
            "|                    |  PCIe x1 Slot  |                          |",
            "|                    +----------------+                          |",
            "|                                                                |",
            "|                    +----------------+                          |",
            "|                    |  PCIe x1 Slot  |                          |",
            "|                    +----------------+                          |",
        ],
        "gpu": [
            "|   +------+                                                    |",
            "|   | GPU  |-------                                             |",
            "|   +------+                                                    |",
        ],
    }

    # Create the fog of war map (start with empty frame)
    fog_map = empty_frame.copy()

    # Add title
    fog_map[1] = "|             KodeKloud Computer Quest Exploration Map          |"

    # Dictionary of positions for each component in the map
    # The position is (row, column) where the marker will be placed
    positions = {
        "kernel": (7, 8),  # OS Kernel
        "virtual_memory": (12, 8),  # Virtual Memory
        "cpu_package": (7, 36),  # CPU Package
        "core1": (9, 15),  # Core 1
        "core1_cu": (10, 13),  # Core 1 CU
        "core1_alu": (10, 17),  # Core 1 ALU
        "core1_registers": (11, 13),  # Core 1 Registers
        "core1_l1": (11, 17),  # Core 1 L1
        "core2": (9, 38),  # Core 2
        "core2_cu": (10, 36),  # Core 2 CU
        "core2_alu": (10, 40),  # Core 2 ALU
        "core2_registers": (11, 36),  # Core 2 Registers
        "core2_l1": (11, 40),  # Core 2 L1
        "l2_cache1": (15, 15),  # L2 Cache 1
        "l2_cache2": (15, 38),  # L2 Cache 2
        "l3_cache": (19, 30),  # L3 Cache
        "ram_dimm1": (19, 8),  # RAM DIMM 1
        "ram_dimm2": (23, 8),  # RAM DIMM 2
        "ram_dimm3": (27, 8),  # RAM DIMM 3
        "ram_dimm4": (31, 8),  # RAM DIMM 4
        "pch": (29, 36),  # PCH
        "storage_controller": (32, 15),  # Storage Controller
        "pcie_controller": (32, 38),  # PCIe Controller
        "network_interface": (37, 15),  # Network Interface
        "bios": (37, 38),  # BIOS/UEFI
        "ssd": (36, 8),  # SSD
        "hdd": (40, 8),  # HDD
        "sata_ports": (45, 16),  # SATA Ports
        "usb_ports": (45, 36),  # USB Ports
        "ethernet": (45, 51),  # Ethernet
        "pcie_x16": (49, 28),  # PCIe x16 Slot
        "gpu": (49, 8),  # GPU
        "pcie_x1_1": (53, 28),  # PCIe x1 Slot 1
        "pcie_x1_2": (57, 28),  # PCIe x1 Slot 2
    }

    # Component groups for revealing sections on the map
    component_groups = {
        "cpu_package": ["cpu_package"],
        "kernel": ["kernel"],
        "virtual_memory": ["virtual_memory"],
        "core1": ["core1"],
        "core_components": [
            "core1_cu",
            "core1_alu",
            "core1_registers",
            "core1_l1",
            "core2_cu",
            "core2_alu",
            "core2_registers",
            "core2_l1",
        ],
        "core2": ["core2"],
        "l2_cache": ["l2_cache1", "l2_cache2"],
        "l3_cache": ["l3_cache"],
        "ram_dimm1": ["ram_dimm1"],
        "ram_dimm2": ["ram_dimm2"],
        "ram_dimm3": ["ram_dimm3"],
        "ram_dimm4": ["ram_dimm4"],
        "pch": ["pch"],
        "pch_controllers": ["storage_controller", "pcie_controller"],
        "pch_components": ["network_interface", "bios"],
        "storage": ["ssd", "hdd"],
        "io_ports": ["sata_ports", "usb_ports", "ethernet"],
        "pcie_slots": ["pcie_x16", "pcie_x1_1", "pcie_x1_2"],
        "gpu": ["gpu"],
    }

    # Track which component parts to reveal based on visited rooms
    revealed_parts = set()

    # Check which rooms have been visited and mark parts to reveal
    for room_id, room_data in map_grid.items():
        if room_data["visited"]:
            # Add revealed component parts based on visited rooms
            for group_name, group_rooms in component_groups.items():
                if room_id in group_rooms:
                    revealed_parts.add(group_name)

            # Special case for connections between components
            if room_id == "cpu_package" or room_id == "pch":
                revealed_parts.add("dmi_link")

            if room_id in [
                "core1",
                "core2",
                "core1_cu",
                "core1_alu",
                "core1_registers",
                "core1_l1",
            ]:
                revealed_parts.add("core_components")

    # Reveal map sections based on exploration
    for part_name in revealed_parts:
        if part_name in component_parts:
            part_lines = component_parts[part_name]

            # Determine where to place these component lines
            if part_name == "kernel":
                start_row = 5
            elif part_name == "virtual_memory":
                start_row = 10
            elif part_name == "cpu_package":
                start_row = 5
            elif part_name == "core1":
                start_row = 8
            elif part_name == "core2":
                start_row = 8
            elif part_name == "core_components":
                start_row = 10
            elif part_name == "l2_cache":
                start_row = 14
            elif part_name == "l3_cache":
                start_row = 18
            elif part_name == "ram_dimm1":
                start_row = 18
            elif part_name == "ram_dimm2":
                start_row = 22
            elif part_name == "ram_dimm3":
                start_row = 26
            elif part_name == "ram_dimm4":
                start_row = 30
            elif part_name == "dmi_link":
                start_row = 23
            elif part_name == "pch":
                start_row = 27
            elif part_name == "pch_controllers":
                start_row = 31
            elif part_name == "pch_components":
                start_row = 36
            elif part_name == "storage":
                start_row = 35
            elif part_name == "io_ports":
                start_row = 44
            elif part_name == "pcie_slots":
                start_row = 48
            elif part_name == "gpu":
                start_row = 48
            else:
                start_row = 1

            # Merge the component part into the fog map
            for i, line in enumerate(part_lines):
                if start_row + i < len(fog_map):
                    # Preserve the map border
                    base_line = fog_map[start_row + i]
                    for j in range(min(len(line), len(base_line))):
                        if line[j] != " " and j > 0 and j < len(base_line) - 1:
                            chars = list(base_line)
                            chars[j] = line[j]
                            base_line = "".join(chars)
                    fog_map[start_row + i] = base_line

    # Add markers for visited rooms and current location
    player_location = game.player.location
    for room_id, room in game.game_map.rooms.items():
        if room_id in positions and room_id in map_grid and map_grid[room_id]["visited"]:
            row, col = positions[room_id]

            if row < len(fog_map) and col < len(fog_map[row]):
                # Mark current location with ★, visited locations with •
                if room == player_location:
                    marker = "★"
                else:
                    marker = "•"

                # Apply the marker
                line = fog_map[row]
                if col < len(line):
                    fog_map[row] = line[:col] + marker + line[col + 1 :]

    # Combine the fog map into a string
    map_str = "YOUR EXPLORATION MAP\n"
    map_str += "===================\n\n"

    for line in fog_map:
        map_str += line + "\n"

    map_str += "\nLEGEND:\n"
    map_str += "------\n"
    map_str += "• = Visited Location\n"
    map_str += "★ = Current Location\n\n"

    # Add current location and available connections
    map_str += f"You are currently in: {player_location.name}\n"

    # Add connections from current location
    if player_location.doors:
        map_str += "Available connections:\n"
        for direction, connected_room in player_location.doors.items():
            from computerquest.config import DIRECTION_NAMES

            # Convert direction code to readable text
            dir_text = DIRECTION_NAMES.get(direction, direction)

            map_str += f"- {dir_text}: {connected_room.name}\n"

    # Add note about the motherboard command
    map_str += "\nTip: Use the 'motherboard' command to see the full diagram."

    return map_str
