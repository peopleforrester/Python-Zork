#!/usr/bin/env python3
"""
Unit tests for the ComputerArchitecture class
"""

import unittest
from unittest.mock import patch

from computerquest.models.player import Player
from computerquest.world.architecture import ComputerArchitecture


class TestComputerArchitecture(unittest.TestCase):
    """Test cases for the ComputerArchitecture class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create architecture with setup mocked
        with patch.object(ComputerArchitecture, 'setup'):
            self.arch = ComputerArchitecture()

    def test_init(self):
        """Test architecture initialization"""
        self.assertIsNone(self.arch.player)
        self.assertEqual(self.arch.rooms, {})
        self.assertEqual(self.arch.name, "KodeKloud Computer Quest")

    def test_setup(self):
        """Test full setup process"""
        # Use real setup with subcomponents mocked. patch.object on a class
        # method records bound-instance calls without an explicit self arg.
        with patch.object(ComputerArchitecture, 'make_components') as m_make, \
             patch.object(ComputerArchitecture, 'connect_components') as m_connect, \
             patch.object(ComputerArchitecture, 'create_items') as m_items, \
             patch.object(ComputerArchitecture, 'create_player') as m_player, \
             patch.object(ComputerArchitecture, 'bind_puzzles') as m_bind:

            self.arch.setup()

            m_make.assert_called_once_with()
            m_connect.assert_called_once_with()
            m_items.assert_called_once_with()
            m_player.assert_called_once_with()
            m_bind.assert_called_once_with()

    def test_make_components(self):
        """Test making components"""
        # Call the real method
        self.arch.make_components()

        # Check rooms dictionary
        self.assertGreater(len(self.arch.rooms), 0)

        # Check some specific components
        self.assertIn("cpu_package", self.arch.rooms)
        self.assertIn("core1", self.arch.rooms)
        self.assertIn("memory_controller", self.arch.rooms)
        self.assertIn("ram_dimm1", self.arch.rooms)
        self.assertIn("network_interface", self.arch.rooms)
        self.assertIn("bios", self.arch.rooms)
        self.assertIn("ssd", self.arch.rooms)
        self.assertIn("kernel", self.arch.rooms)

        # Check component properties
        cpu = self.arch.rooms["cpu_package"]
        self.assertEqual(cpu.name, "CPU Package")
        self.assertTrue(cpu.lit)
        self.assertEqual(cpu.id, "CPU000")

        # Check properties of other component types
        ram = self.arch.rooms["ram_dimm1"]
        self.assertEqual(ram.name, "RAM DIMM 1")
        self.assertTrue("volatile memory" in ram.desc.lower())

        network = self.arch.rooms["network_interface"]
        self.assertTrue("network" in network.name.lower())
        self.assertTrue("packet" in network.desc.lower())

    def test_connect_components(self):
        """Test connecting components"""
        # Make components first
        self.arch.make_components()

        # Test initial state
        cpu = self.arch.rooms["cpu_package"]
        self.assertEqual(len(cpu.doors), 0)
        self.assertEqual(len(cpu.openDoors), 0)

        # Connect components
        self.arch.connect_components()

        # Check CPU connections
        cpu = self.arch.rooms["cpu_package"]
        self.assertGreater(len(cpu.doors), 0)

        # Check specific connections
        self.assertIn("n", cpu.doors)  # North to core1
        self.assertEqual(cpu.doors["n"], self.arch.rooms["core1"])

        self.assertIn("ne", cpu.doors)  # Northeast to core2
        self.assertEqual(cpu.doors["ne"], self.arch.rooms["core2"])

        self.assertIn("s", cpu.doors)  # South to L3 cache
        self.assertEqual(cpu.doors["s"], self.arch.rooms["l3_cache"])

        self.assertIn("d", cpu.doors)  # Down to PCH
        self.assertEqual(cpu.doors["d"], self.arch.rooms["pch"])

        # Check Core 1 connections — its 's' goes to its own L1 cache, not
        # back to cpu_package. The architecture uses some intentionally
        # asymmetric passages.
        core1 = self.arch.rooms["core1"]
        self.assertEqual(core1.doors["s"], self.arch.rooms["core1_l1"])
        self.assertEqual(core1.doors["n"], self.arch.rooms["core1_cu"])

        # Check memory controller connections
        memory_ctrl = self.arch.rooms["memory_controller"]
        self.assertIn("w", memory_ctrl.doors)
        self.assertEqual(memory_ctrl.doors["w"], self.arch.rooms["ram_dimm1"])

        # Check RAM connections
        ram1 = self.arch.rooms["ram_dimm1"]
        self.assertIn("w", ram1.doors)
        self.assertEqual(ram1.doors["w"], self.arch.rooms["kernel"])

        # Check peripheral connections
        pcie_ctrl = self.arch.rooms["pcie_controller"]
        self.assertIn("s", pcie_ctrl.doors)
        self.assertEqual(pcie_ctrl.doors["s"], self.arch.rooms["pcie_x16"])

        # Spot-check a known bidirectional pair (cpu_package <-> l3_cache)
        # rather than enforcing bidirectionality globally.
        l3 = self.arch.rooms["l3_cache"]
        self.assertEqual(cpu.doors["s"], l3)
        self.assertEqual(l3.doors["n"], cpu)

    def test_create_items(self):
        """Test item creation"""
        # Make components first
        self.arch.make_components()

        # Create items
        self.arch.create_items()

        # Check CPU package items
        cpu = self.arch.rooms["cpu_package"]
        self.assertIn("instruction_manual", cpu.items)
        self.assertTrue("Guide" in cpu.items["instruction_manual"])

        # Check core components items
        core1_cu = self.arch.rooms["core1_cu"]
        self.assertIn("decoder_tool", core1_cu.items)

        core1_registers = self.arch.rooms["core1_registers"]
        self.assertIn("register_log", core1_registers.items)

        # Check virus locations
        ssd = self.arch.rooms["ssd"]
        self.assertIn("boot_sector_virus", ssd.items)

        kernel = self.arch.rooms["kernel"]
        self.assertIn("rootkit_virus", kernel.items)

        ram1 = self.arch.rooms["ram_dimm1"]
        self.assertIn("memory_resident_virus", ram1.items)

        bios = self.arch.rooms["bios"]
        self.assertIn("firmware_virus", bios.items)

        network = self.arch.rooms["network_interface"]
        self.assertIn("packet_sniffer_virus", network.items)

    def test_create_player(self):
        """Test player creation"""
        # Make components first
        self.arch.make_components()

        # Create player
        self.arch.create_player()

        # Check player created
        self.assertIsNotNone(self.arch.player)
        self.assertIsInstance(self.arch.player, Player)

        # Check starting location
        self.assertEqual(self.arch.player.location, self.arch.rooms["cpu_package"])

        # Check starting inventory
        self.assertIn("antivirus_tool", self.arch.player.items)
        self.assertIn("system_mapper", self.arch.player.items)

        # Check player name
        self.assertEqual(self.arch.player.name, "Security Program")

if __name__ == "__main__":
    unittest.main()


class TestPuzzleBindings(unittest.TestCase):
    """Microquiz step 3: rooms declare their puzzles; bindings must resolve."""

    @classmethod
    def setUpClass(cls) -> None:
        with patch.object(ComputerArchitecture, "setup"):
            cls.arch = ComputerArchitecture()
        cls.arch.make_components()
        cls.arch.bind_puzzles()

    def test_every_room_has_a_puzzles_list(self) -> None:
        for room_id, room in self.arch.rooms.items():
            self.assertIsInstance(room.puzzles, list, room_id)

    def test_seed_bindings(self) -> None:
        self.assertEqual(
            self.arch.rooms["core1_l1"].puzzles,
            ["l1_lru_basic", "l1_associativity_2way"],
        )
        self.assertEqual(self.arch.rooms["core1"].puzzles, ["pipeline_forwarding_intro"])

    def test_bound_ids_resolve_and_respect_the_cap(self) -> None:
        from computerquest.mechanics.puzzles import load_registry

        registry = load_registry()
        seen: set[str] = set()
        for room_id, room in self.arch.rooms.items():
            self.assertLessEqual(len(room.puzzles), 3, f"{room_id} exceeds cap (decision 1)")
            for puzzle_id in room.puzzles:
                self.assertIn(puzzle_id, registry.by_id, f"{room_id} binds unknown {puzzle_id}")
                self.assertNotIn(puzzle_id, seen, f"{puzzle_id} bound to two rooms")
                seen.add(puzzle_id)

    def test_all_shipped_puzzles_are_bound_somewhere(self) -> None:
        from computerquest.mechanics.puzzles import load_registry

        bound = {p for room in self.arch.rooms.values() for p in room.puzzles}
        self.assertSetEqual(bound, set(load_registry().by_id))


class TestWorldGraphInvariants(unittest.TestCase):
    """Every room must be reachable, and no connect_to call may silently
    overwrite an earlier door on the same direction (the bug that orphaned
    l2_cache2 and ram_dimm4)."""

    @classmethod
    def setUpClass(cls) -> None:
        with patch.object(ComputerArchitecture, "setup"):
            cls.arch = ComputerArchitecture()
        cls.arch.make_components()
        cls.arch.connect_components()

    def test_every_room_reachable_from_start(self) -> None:
        from collections import deque

        rooms = self.arch.rooms
        reverse = {room: rid for rid, room in rooms.items()}
        seen = {"cpu_package"}
        queue = deque(["cpu_package"])
        while queue:
            rid = queue.popleft()
            for dest in rooms[rid].doors.values():
                did = reverse.get(dest)
                if did and did not in seen:
                    seen.add(did)
                    queue.append(did)
        self.assertSetEqual(set(rooms), seen, f"unreachable: {sorted(set(rooms) - seen)}")

    def test_no_direction_collisions(self) -> None:
        from collections import Counter

        from computerquest.models.component import Component

        calls: list[tuple[str, str]] = []
        original = Component.connect_to

        def spy(room, other, direction):
            calls.append((room.name, direction))
            return original(room, other, direction)

        with patch.object(ComputerArchitecture, "setup"):
            arch = ComputerArchitecture()
        arch.make_components()
        with patch.object(Component, "connect_to", spy):
            arch.connect_components()

        dupes = [key for key, n in Counter(calls).items() if n > 1]
        self.assertEqual(dupes, [], f"door overwrites: {dupes}")
