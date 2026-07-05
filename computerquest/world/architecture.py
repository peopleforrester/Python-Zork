"""
Architecture module for creating the computer system

Handles creation and connection of computer components
"""

from computerquest.models.component import Component
from computerquest.models.player import Player


class ComputerArchitecture:
    """Creates and manages the computer architecture world"""
    def __init__(self):
        self.player = None
        self.rooms = {}
        self.name = "KodeKloud Computer Quest"

    def setup(self):
        """
        Setup the complete computer architecture world
        """
        self.make_components()
        self.connect_components()
        self.create_items()
        self.create_player()
        self.bind_puzzles()

    def bind_puzzles(self):
        """
        Bind micro-puzzle ids to their rooms (declarative, reviewable in one
        place per the microquiz contract). Max three per room (decision 1);
        ids must exist in mechanics/puzzles/data/ — tests enforce both.
        """
        self.rooms["core1_l1"].puzzles = ["l1_lru_basic", "l1_associativity_2way"]
        self.rooms["core1"].puzzles = ["pipeline_forwarding_intro"]

    def make_components(self):
        """
        Create all computer components
        """
        # CPU Package components
        self.rooms["cpu_package"] = Component(
            "CPU Package",
            "You are inside the main CPU package, the brain of the computer. This sophisticated silicon die houses multiple cores, cache memory levels, and the integrated memory controller. The environment hums with activity as billions of calculations occur every second.",
            True,
            "CPU000"
        )

        # Core 1 components
        self.rooms["core1"] = Component(
            "Core 1",
            "You're inside the first CPU core. This processing unit contains its own control unit, ALU, registers, and L1 cache. The air crackles with electrical impulses as instructions are decoded and executed.",
            True,
            "CORE1"
        )

        self.rooms["core1_cu"] = Component(
            "Core 1 Control Unit",
            "The control unit of Core 1 coordinates operations, fetching and decoding instructions. Status indicators flash in complex patterns as it orchestrates the execution pipeline.",
            True,
            "CU001"
        )

        self.rooms["core1_alu"] = Component(
            "Core 1 ALU",
            "The Arithmetic Logic Unit of Core 1 performs all mathematical and logical operations. Numbers and boolean values flow through circuits as computations occur at incredible speed.",
            True,
            "ALU001"
        )

        self.rooms["core1_registers"] = Component(
            "Core 1 Registers",
            "These small, ultra-fast storage locations hold data being actively processed by Core 1. Each register glows with changing values as operations proceed.",
            True,
            "REG001"
        )

        self.rooms["core1_l1"] = Component(
            "Core 1 L1 Cache",
            "The Level 1 cache for Core 1 - the fastest and smallest memory in the hierarchy. Split into instruction and data sections, it provides near-instant access to frequently used information.",
            True,
            "L1C001"
        )

        # Core 2 components (similar structure)
        self.rooms["core2"] = Component(
            "Core 2",
            "You're inside the second CPU core. Like Core 1, this processing unit contains its own control unit, ALU, registers, and L1 cache, allowing parallel execution of instructions.",
            True,
            "CORE2"
        )

        self.rooms["core2_cu"] = Component(
            "Core 2 Control Unit",
            "The control unit of Core 2 coordinates operations, fetching and decoding instructions. Status indicators flash in complex patterns as it orchestrates the execution pipeline.",
            True,
            "CU002"
        )

        self.rooms["core2_alu"] = Component(
            "Core 2 ALU",
            "The Arithmetic Logic Unit of Core 2 performs all mathematical and logical operations. Numbers and boolean values flow through circuits as computations occur at incredible speed.",
            True,
            "ALU002"
        )

        self.rooms["core2_registers"] = Component(
            "Core 2 Registers",
            "These small, ultra-fast storage locations hold data being actively processed by Core 2. Each register glows with changing values as operations proceed.",
            True,
            "REG002"
        )

        self.rooms["core2_l1"] = Component(
            "Core 2 L1 Cache",
            "The Level 1 cache for Core 2 - the fastest and smallest memory in the hierarchy. Split into instruction and data sections, it provides near-instant access to frequently used information.",
            True,
            "L1C002"
        )

        # Level 2 Cache
        self.rooms["l2_cache1"] = Component(
            "Core 1 L2 Cache",
            "The L2 cache for Core 1 - larger but slightly slower than L1. This dedicated cache serves only this core, providing a middle tier in the memory hierarchy.",
            True,
            "L2C001"
        )

        self.rooms["l2_cache2"] = Component(
            "Core 2 L2 Cache",
            "The L2 cache for Core 2 - similar to Core 1's L2 cache, it provides dedicated secondary caching for this core only.",
            True,
            "L2C002"
        )

        # L3 Cache (shared)
        self.rooms["l3_cache"] = Component(
            "L3 Cache",
            "The Level 3 cache, shared between all CPU cores. Much larger than L1 or L2, but slower. This serves as the last line of cache before memory requests must go to RAM.",
            True,
            "L3C000"
        )

        # Memory Controller
        self.rooms["memory_controller"] = Component(
            "Memory Controller",
            "The integrated memory controller manages all communication between the CPU and RAM. Once a separate component, it's now built into the CPU package for improved performance.",
            True,
            "MC000"
        )

        # RAM DIMMs
        self.rooms["ram_dimm1"] = Component(
            "RAM DIMM 1",
            "You're inside the first RAM module. This volatile memory stores active programs and data. The space is vast compared to caches, with electrical charges representing binary data.",
            True,
            "RAM001"
        )

        self.rooms["ram_dimm2"] = Component(
            "RAM DIMM 2",
            "The second RAM module, identical to DIMM 1 but addressing a different memory range. Together with the other modules, they form the system's main memory.",
            True,
            "RAM002"
        )

        self.rooms["ram_dimm3"] = Component(
            "RAM DIMM 3",
            "The third RAM module in the system, expanding the total memory capacity available to programs.",
            True,
            "RAM003"
        )

        self.rooms["ram_dimm4"] = Component(
            "RAM DIMM 4",
            "The fourth RAM module, completing the system's memory configuration. Data moves constantly between here and the CPU as programs execute.",
            True,
            "RAM004"
        )

        # OS Kernel (conceptual)
        self.rooms["kernel"] = Component(
            "OS Kernel",
            "The core of the operating system, loaded into RAM at boot. This protected environment controls hardware resources and provides services to applications. Though residing in RAM physically, it appears as a distinct environment.",
            True,
            "KRN001"
        )

        # Virtual Memory (conceptual)
        self.rooms["virtual_memory"] = Component(
            "Virtual Memory",
            "A conceptual space where the operating system creates the illusion of more memory than physically available. Pages of data move between RAM and storage as needed.",
            True,
            "VM001"
        )

        # PCH components
        self.rooms["pch"] = Component(
            "Platform Controller Hub",
            "You've entered the PCH - the modern replacement for the traditional Northbridge and Southbridge chipsets. This hub manages most of the computer's I/O functions.",
            True,
            "PCH001"
        )

        self.rooms["storage_controller"] = Component(
            "Storage Controller",
            "This component within the PCH manages all storage devices. It translates system requests into the specific protocols needed by different storage media.",
            True,
            "STC001"
        )

        self.rooms["pcie_controller"] = Component(
            "PCIe Controller",
            "The PCIe Controller manages the high-speed expansion slots used for graphics cards and other peripherals. Information flows through multiple lanes at different speeds based on the connected device's capabilities.",
            True,
            "PCIE001"
        )

        self.rooms["network_interface"] = Component(
            "Network Interface",
            "The network controller enables communication with other computers. Data packets are assembled and disassembled here, following precise networking protocols.",
            True,
            "NET001"
        )

        self.rooms["bios"] = Component(
            "BIOS/UEFI Flash",
            "The firmware that initializes hardware during boot. This ancient-seeming area contains the basic instructions that bring the computer to life.",
            True,
            "BIOS001"
        )

        # Storage components
        self.rooms["sata_ports"] = Component(
            "SATA Ports",
            "The connection points for storage devices. These standardized interfaces allow the system to communicate with SSDs and HDDs.",
            True,
            "SATA001"
        )

        self.rooms["ssd"] = Component(
            "Solid State Drive",
            "The system's primary storage device. Unlike the constantly changing memory areas, data here is organized in flash memory cells that retain information when powered off.",
            True,
            "SSD001"
        )

        self.rooms["hdd"] = Component(
            "Hard Disk Drive",
            "The mechanical storage device with spinning platters and moving read/write heads. While slower than the SSD, it offers larger capacity for data storage.",
            True,
            "HDD001"
        )

        # PCIe slots and GPU
        self.rooms["pcie_x16"] = Component(
            "PCIe x16 Slot",
            "The high-bandwidth expansion slot primarily used for graphics cards. 16 lanes of data can transfer simultaneously, enabling the fastest possible communication.",
            True,
            "PCIEX16"
        )

        self.rooms["pcie_x1_1"] = Component(
            "PCIe x1 Slot 1",
            "A smaller expansion slot with a single data lane, used for less bandwidth-intensive devices like sound cards or additional USB controllers.",
            True,
            "PCIEX11"
        )

        self.rooms["pcie_x1_2"] = Component(
            "PCIe x1 Slot 2",
            "Another single-lane expansion slot, identical to the first PCIe x1 slot but at a different physical location on the motherboard.",
            True,
            "PCIEX12"
        )

        self.rooms["gpu"] = Component(
            "Graphics Processing Unit",
            "The GPU is a massive parallel processing environment. Thousands of small cores work simultaneously on graphics rendering tasks. Visual data streams all around you.",
            True,
            "GPU001"
        )

        # External ports
        self.rooms["usb_ports"] = Component(
            "USB Ports",
            "The connection points for external USB devices. These versatile interfaces support a wide variety of peripherals.",
            True,
            "USB001"
        )

        self.rooms["ethernet"] = Component(
            "Ethernet Port",
            "The connection point for wired networking. High-speed data transfers occur here, linking this computer to the broader network.",
            True,
            "ETH001"
        )

    def connect_components(self):
        """
        Connect all components according to modern computer architecture
        """
        # Connect CPU Package to cores and caches
        self.rooms["cpu_package"].connect_to(self.rooms["core1"], 'n')
        self.rooms["cpu_package"].connect_to(self.rooms["core2"], 'ne')
        self.rooms["cpu_package"].connect_to(self.rooms["l3_cache"], 's')

        # Connect Core 1 to its components
        self.rooms["core1"].connect_to(self.rooms["core1_cu"], 'n')
        self.rooms["core1"].connect_to(self.rooms["core1_alu"], 'e')
        self.rooms["core1"].connect_to(self.rooms["core1_registers"], 'w')
        self.rooms["core1"].connect_to(self.rooms["core1_l1"], 's')
        self.rooms["core1"].connect_to(self.rooms["l2_cache1"], 'se')

        # Add return connections for Core 1 components
        self.rooms["core1_cu"].connect_to(self.rooms["core1"], 's')
        self.rooms["core1_alu"].connect_to(self.rooms["core1"], 'w')
        self.rooms["core1_registers"].connect_to(self.rooms["core1"], 'e')
        self.rooms["core1_l1"].connect_to(self.rooms["core1"], 'n')

        # Connect Core 2 to its components
        self.rooms["core2"].connect_to(self.rooms["core2_cu"], 'n')
        self.rooms["core2"].connect_to(self.rooms["core2_alu"], 'e')
        self.rooms["core2"].connect_to(self.rooms["core2_registers"], 'w')
        self.rooms["core2"].connect_to(self.rooms["core2_l1"], 's')
        self.rooms["core2"].connect_to(self.rooms["l2_cache2"], 'sw')
        self.rooms["core2"].connect_to(self.rooms["cpu_package"], 'sw')

        # Add return connections for Core 2 components
        self.rooms["core2_cu"].connect_to(self.rooms["core2"], 's')
        self.rooms["core2_alu"].connect_to(self.rooms["core2"], 'w')
        self.rooms["core2_registers"].connect_to(self.rooms["core2"], 'e')
        self.rooms["core2_l1"].connect_to(self.rooms["core2"], 'n')

        # Connect L2 and L3 caches
        self.rooms["l2_cache1"].connect_to(self.rooms["core1"], 'nw')  # Return path to Core 1
        self.rooms["l2_cache1"].connect_to(self.rooms["l3_cache"], 's')
        self.rooms["l2_cache2"].connect_to(self.rooms["core2"], 'n')   # Return path to Core 2
        self.rooms["l2_cache2"].connect_to(self.rooms["l3_cache"], 's')

        # Connect L3 to Memory Controller and back to CPU Package
        self.rooms["l3_cache"].connect_to(self.rooms["memory_controller"], 's')
        self.rooms["l3_cache"].connect_to(self.rooms["cpu_package"], 'n')  # Return path

        # Connect Memory Controller to RAM
        self.rooms["memory_controller"].connect_to(self.rooms["ram_dimm1"], 'w')
        self.rooms["memory_controller"].connect_to(self.rooms["ram_dimm2"], 'sw')
        self.rooms["memory_controller"].connect_to(self.rooms["ram_dimm3"], 'nw')
        self.rooms["memory_controller"].connect_to(self.rooms["ram_dimm4"], 'n')
        self.rooms["memory_controller"].connect_to(self.rooms["l3_cache"], 'n')  # Return path

        # Connect RAM to conceptual components and back to memory controller
        self.rooms["ram_dimm1"].connect_to(self.rooms["kernel"], 'w')
        self.rooms["ram_dimm1"].connect_to(self.rooms["memory_controller"], 'e')  # Return path

        self.rooms["ram_dimm2"].connect_to(self.rooms["virtual_memory"], 'w')
        self.rooms["ram_dimm2"].connect_to(self.rooms["memory_controller"], 'ne')  # Return path

        self.rooms["ram_dimm3"].connect_to(self.rooms["memory_controller"], 'se')  # Return path
        self.rooms["ram_dimm4"].connect_to(self.rooms["memory_controller"], 's')   # Return path

        # Connect conceptual components back to RAM
        self.rooms["kernel"].connect_to(self.rooms["ram_dimm1"], 'e')
        self.rooms["virtual_memory"].connect_to(self.rooms["ram_dimm2"], 'e')

        # Connect CPU Package to PCH via DMI Link (bidirectional)
        self.rooms["cpu_package"].connect_to(self.rooms["pch"], 'd')  # Down represents the DMI Link
        self.rooms["pch"].connect_to(self.rooms["cpu_package"], 'u')  # Up to return to CPU

        # Connect PCH to its internal components (with return paths)
        self.rooms["pch"].connect_to(self.rooms["storage_controller"], 'n')
        self.rooms["storage_controller"].connect_to(self.rooms["pch"], 's')  # Return path

        self.rooms["pch"].connect_to(self.rooms["pcie_controller"], 'e')
        self.rooms["pcie_controller"].connect_to(self.rooms["pch"], 'w')  # Return path

        self.rooms["pch"].connect_to(self.rooms["network_interface"], 's')
        self.rooms["network_interface"].connect_to(self.rooms["pch"], 'n')  # Return path

        self.rooms["pch"].connect_to(self.rooms["bios"], 'w')
        self.rooms["bios"].connect_to(self.rooms["pch"], 'e')  # Return path

        # Connect storage components (with return paths)
        self.rooms["storage_controller"].connect_to(self.rooms["sata_ports"], 'w')
        self.rooms["sata_ports"].connect_to(self.rooms["storage_controller"], 'e')  # Return path

        self.rooms["sata_ports"].connect_to(self.rooms["ssd"], 'nw')
        self.rooms["ssd"].connect_to(self.rooms["sata_ports"], 'se')  # Return path

        self.rooms["sata_ports"].connect_to(self.rooms["hdd"], 'sw')
        self.rooms["hdd"].connect_to(self.rooms["sata_ports"], 'ne')  # Return path

        # Connect PCIe components (with return paths)
        self.rooms["pcie_controller"].connect_to(self.rooms["pcie_x16"], 's')
        self.rooms["pcie_x16"].connect_to(self.rooms["pcie_controller"], 'n')  # Return path

        self.rooms["pcie_controller"].connect_to(self.rooms["pcie_x1_1"], 'se')
        self.rooms["pcie_x1_1"].connect_to(self.rooms["pcie_controller"], 'nw')  # Return path

        self.rooms["pcie_controller"].connect_to(self.rooms["pcie_x1_2"], 'sw')
        self.rooms["pcie_x1_2"].connect_to(self.rooms["pcie_controller"], 'ne')  # Return path

        self.rooms["pcie_x16"].connect_to(self.rooms["gpu"], 'w')
        self.rooms["gpu"].connect_to(self.rooms["pcie_x16"], 'e')  # Return path

        # Connect external ports (with return paths)
        self.rooms["pch"].connect_to(self.rooms["usb_ports"], 'ne')
        self.rooms["usb_ports"].connect_to(self.rooms["pch"], 'sw')  # Return path

        self.rooms["pch"].connect_to(self.rooms["ethernet"], 'se')
        self.rooms["ethernet"].connect_to(self.rooms["pch"], 'nw')  # Return path

        # Connect Virtual Memory to storage (conceptual link)
        self.rooms["virtual_memory"].connect_to(self.rooms["storage_controller"], 's')
        self.rooms["storage_controller"].connect_to(self.rooms["virtual_memory"], 'n')  # Return path

    def create_items(self):
        """
        Create items for computer components including tools and viruses
        """
        # Tools and useful items
        self.rooms["cpu_package"].add_items({
            'instruction_manual': '# System Architecture Guide\n\nWelcome to KodeKloud Computer Quest!\n\nYou are inside a computer system infected with multiple viruses. Your mission is to explore the system, learn about computer architecture, and locate all the viruses hiding in different components.\n\nBasic commands:\n-go : followed by a direction (n, s, e, w, up, down)\n-take : pick up an item\n-look : examine your surroundings or a specific item\n-read : read text content of items\n-scan : use on areas to detect virus presence\n-quarantine : use on viruses once found\n\nThe system has multiple levels, from the CPU to storage to networking. Each area represents a real computer architecture component with its own function. Learn about them as you explore!'
        })

        self.rooms["core1_cu"].add_items({
            'decoder_tool': 'An instruction decoder tool that can help analyze suspicious code patterns.'
        })

        self.rooms["core1_registers"].add_items({
            'register_log': 'A log showing recent register state changes. Some unusual patterns are highlighted.'
        })

        # Add items to Core 2 components
        self.rooms["core2_cu"].add_items({
            'parallel_instructions': 'A guide showing how the control unit manages parallel instruction execution across multiple cores.'
        })

        self.rooms["core2_alu"].add_items({
            'vector_operations': 'Documentation about SIMD (Single Instruction, Multiple Data) vector operations that process multiple data points simultaneously.'
        })

        self.rooms["core2_registers"].add_items({
            'thread_state': 'A snapshot of register states showing how different threads maintain separate execution contexts.'
        })

        # Clues and viruses - note the new locations matching the updated architecture
        self.rooms["core1_alu"].add_items({
            'strange_calculation': 'A record of unusual calculation patterns that seem to be used for encryption.'
        })

        self.rooms["l3_cache"].add_items({
            'memory_leak': 'Evidence of a program gradually consuming more memory than it should.'
        })

        # The viruses - in their specific locations matching the updated diagram
        self.rooms["ssd"].add_items({
            'boot_sector_virus': 'A virus that has infected the boot sector of the drive, activating before the operating system loads.'
        })

        self.rooms["kernel"].add_items({
            'rootkit_virus': 'A sophisticated rootkit that has embedded itself in the kernel, hiding its presence from standard detection methods.'
        })

        self.rooms["ram_dimm1"].add_items({
            'memory_resident_virus': 'A virus that stays entirely in RAM, modifying programs as they are loaded from storage.'
        })

        self.rooms["bios"].add_items({
            'firmware_virus': 'A virus that has infected the system firmware, persisting even through operating system reinstalls.'
        })

        self.rooms["network_interface"].add_items({
            'packet_sniffer_virus': 'A virus that captures and redirects sensitive network traffic.'
        })

    def create_player(self):
        """
        Create player object with starting position and inventory
        """
        player_items = {
            'antivirus_tool': 'A basic antivirus scanner that can detect and quarantine viruses once they\'re found.',
            'system_mapper': 'A tool showing a map of the computer architecture you\'ve explored so far.'
        }

        # Start the player in the CPU Package
        self.player = Player(self.rooms["cpu_package"], player_items, False, "Security Program")
