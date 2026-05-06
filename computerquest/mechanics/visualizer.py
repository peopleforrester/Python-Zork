"""
ABOUTME: ASCII visualizers for educational architecture diagrams.
ABOUTME: Extracted from game.py in Step 3.1; consumed by Game.handle_visualization.
"""


class ComponentVisualizer:
    def render_cpu_text(self, clock_speed=3.6, cores=4, cache=8):
        """Visualize CPU architecture in text-only mode"""
        result = "++" + "-" * 50 + "++\n"
        result += "|" + "CPU ARCHITECTURE".center(52) + "|\n"
        result += (
            "|"
            + f"Clock Speed: {clock_speed}GHz | Cores: {cores} | Cache: {cache}MB".center(52)
            + "|\n"
        )
        result += "+" + "-" * 50 + "+\n"

        # ASCII art CPU
        cpu_art = [
            "    +---------------------------+    ",
            "    |                           |    ",
            "    |    +-----+     +-----+    |    ",
            "    |    |CPU 1|     |CPU 2|    |    ",
            "    |    +-----+     +-----+    |    ",
            "    |                           |    ",
            "    |    +-----+     +-----+    |    ",
            "    |    |CPU 3|     |CPU 4|    |    ",
            "    |    +-----+     +-----+    |    ",
            "    |                           |    ",
            "    |    +-------------------+  |    ",
            "    |    |     L3 Cache      |  |    ",
            "    |    +-------------------+  |    ",
            "    |                           |    ",
            "    +---------------------------+    ",
            "       | | | | | | | | | | | |      ",
            "       v v v v v v v v v v v v      ",
        ]

        for line in cpu_art:
            result += "|" + line.center(52) + "|\n"

        result += "+" + "-" * 50 + "+\n\n"

        # Educational text
        info_text = [
            "CPU (Central Processing Unit):",
            "- Executes instructions to process data",
            "- Contains multiple cores for parallel processing",
            "- Uses cache memory for faster data access",
            "- Clock speed determines how many cycles per second",
            "- Connected to system via socket on motherboard",
        ]

        for line in info_text:
            result += line + "\n"

        return result

    def render_memory_hierarchy_text(self):
        """Visualize memory hierarchy in text-only mode"""
        result = "++" + "-" * 50 + "++\n"
        result += "|" + "MEMORY HIERARCHY".center(52) + "|\n"
        result += "+" + "-" * 50 + "+\n\n"

        # Memory levels
        levels = [
            {"name": "CPU Registers", "size": "KB", "speed": "0.5ns", "width": 10},
            {"name": "L1 Cache", "size": "64KB", "speed": "1ns", "width": 16},
            {"name": "L2 Cache", "size": "256KB", "speed": "3ns", "width": 22},
            {"name": "L3 Cache", "size": "8MB", "speed": "10ns", "width": 28},
            {"name": "RAM", "size": "16GB", "speed": "100ns", "width": 34},
            {"name": "SSD", "size": "1TB", "speed": "10μs", "width": 40},
            {"name": "HDD", "size": "4TB", "speed": "10ms", "width": 46},
        ]

        for i, level in enumerate(levels):
            box_width = level["width"]
            padding = (50 - box_width) // 2
            result += "|" + " " * padding + "+" + "-" * box_width + "+" + " " * padding + "|\n"

            name_line = f"{level['name']} ({level['size']} | {level['speed']})"
            name_padding = (box_width - len(name_line)) // 2
            if name_padding < 0:
                name_padding = 0
                name_line = name_line[:box_width]

            result += (
                "|"
                + " " * padding
                + "|"
                + " " * name_padding
                + name_line
                + " " * (box_width - len(name_line) - name_padding)
                + "|"
                + " " * padding
                + "|\n"
            )
            result += "|" + " " * padding + "+" + "-" * box_width + "+" + " " * padding + "|\n"

            # Add connecting arrow
            if i < len(levels) - 1:
                result += "|" + " " * 25 + "v" + " " * 26 + "|\n"

        result += "+" + "-" * 50 + "+\n\n"

        # Educational text
        info_text = [
            "Memory Hierarchy:",
            "- Balances speed, size, and cost",
            "- Faster memory is smaller and more expensive",
            "- CPU checks each level in order when requesting data",
            "- Takes advantage of locality of reference",
            "- Hit: Data found at current level",
            "- Miss: Must check next level down",
        ]

        for line in info_text:
            result += line + "\n"

        return result

    def render_network_stack_text(self):
        """Visualize network stack in text-only mode"""
        result = "++" + "-" * 50 + "++\n"
        result += "|" + "NETWORK PROTOCOL STACK".center(52) + "|\n"
        result += "+" + "-" * 50 + "+\n\n"

        layers = [
            "Application Layer (HTTP, FTP, SMTP, DNS)",
            "Transport Layer (TCP, UDP)",
            "Internet Layer (IP, ICMP, ARP)",
            "Link Layer (Ethernet, WiFi, PPP)",
            "Physical Layer (Cables, Radio, Fiber)",
        ]

        for i, layer in enumerate(layers):
            result += "+" + "-" * 50 + "+\n"
            result += "|" + layer.center(50) + "|\n"

            # Add arrow
            if i < len(layers) - 1:
                result += "|" + " " * 24 + "↕" + " " * 25 + "|\n"

        result += "+" + "-" * 50 + "+\n\n"

        # Educational text
        info_text = [
            "Network Protocol Stack:",
            "- Data encapsulation when sending (down)",
            "- Data decapsulation when receiving (up)",
            "- Each layer adds its own headers/trailers",
            "- Provides abstraction between layers",
            "- Each layer has a specific role",
            "- Based on the OSI or TCP/IP model",
        ]

        for line in info_text:
            result += line + "\n"

        return result

    def render_storage_hierarchy_text(self):
        """Visualize storage systems in text-only mode"""
        result = "++" + "-" * 50 + "++\n"
        result += "|" + "STORAGE SYSTEMS".center(52) + "|\n"
        result += "+" + "-" * 50 + "+\n\n"

        # HDD vs SSD
        result += "HDD (Hard Disk Drive)         SSD (Solid State Drive)\n"
        result += "+" + "-" * 24 + "+        +" + "-" * 24 + "+\n"
        result += "|  " + "[]===O".center(20) + "  |        |  " + "[][][][][]".center(20) + "  |\n"
        result += (
            "|  "
            + "Mechanical".center(20)
            + "  |        |  "
            + "No Moving Parts".center(20)
            + "  |\n"
        )
        result += "|  " + "Slower".center(20) + "  |        |  " + "Faster".center(20) + "  |\n"
        result += (
            "|  " + "Magnetic".center(20) + "  |        |  " + "Flash Memory".center(20) + "  |\n"
        )
        result += "+" + "-" * 24 + "+        +" + "-" * 24 + "+\n\n"

        # Data organization
        result += "Data Organization:\n"
        result += "Files → File System → Logical Blocks → Physical Storage\n\n"

        # Educational text
        info_text = [
            "Storage Systems:",
            "- HDD: Mechanical, uses magnetic platters",
            "- SSD: Solid-state, uses flash memory cells",
            "- Data is organized hierarchically",
            "- File systems manage the mapping",
            "- Trade-offs: Speed vs. Capacity vs. Cost",
        ]

        for line in info_text:
            result += line + "\n"

        return result

    def render_motherboard_layout_text(self):
        """Visualize the motherboard layout in text-only mode"""
        result = "++" + "-" * 50 + "++\n"
        result += "|" + "MODERN MOTHERBOARD LAYOUT".center(52) + "|\n"
        result += "+" + "-" * 50 + "+\n\n"

        # Create ASCII representation of the motherboard layout
        layout = [
            "                  CPU PACKAGE                    ",
            "     +-------------------------------------+     ",
            "     |                                     |     ",
            "     |    +-------+          +-------+    |     ",
            "     |    | Core1 |          | Core2 |    |     ",
            "     |    +-------+          +-------+    |     ",
            "     |                                     |     ",
            "     |    +---------------------------+    |     ",
            "     |    |      L3 Cache (Shared)    |    |     ",
            "     |    +---------------------------+    |     ",
            "     +-------------------------------------+     ",
            "                      |                          ",
            "                 DMI Link                        ",
            "                      |                          ",
            "     +-------------------------------------+     ",
            "     |             PCH CHIPSET             |     ",
            "     |                                     |     ",
            "     |  +--------+  +-------+  +--------+ |     ",
            "     |  |Storage |  | PCIe  |  |Network | |     ",
            "     |  |Control |  |Control|  |Interface| |     ",
            "     |  +--------+  +-------+  +--------+ |     ",
            "     |                                     |     ",
            "     |  +--------+                         |     ",
            "     |  |BIOS/UEFI|                        |     ",
            "     |  +--------+                         |     ",
            "     +-------------------------------------+     ",
        ]

        for line in layout:
            result += line + "\n"

        result += "\nVirus Locations:\n"
        result += "- Boot Sector Virus: SSD\n"
        result += "- Rootkit Virus: OS Kernel (in RAM)\n"
        result += "- Memory Resident Virus: RAM DIMM 1\n"
        result += "- Firmware Virus: BIOS/UEFI Flash\n"
        result += "- Packet Sniffer Virus: Network Interface\n"

        return result
