#!/usr/bin/env python3
"""
ABOUTME: Tests for the packet-routing, disk-seek, and signature simulators.
ABOUTME: All expectations hand-derived before implementation.
"""

import unittest

from computerquest.mechanics.simulators.packet import PacketRouteSimulator
from computerquest.mechanics.simulators.signature import SignatureMatchSimulator
from computerquest.mechanics.simulators.storage import SeekDistanceSimulator

ROUTES = {
    "nic": {"kernel": "pch", "ssd": "pch"},
    "pch": {"kernel": "cpu_package", "ssd": "storage_controller"},
    "cpu_package": {"kernel": "kernel"},
    "storage_controller": {"ssd": "ssd"},
}


class TestPacketRoute(unittest.TestCase):
    def test_multi_hop_path(self) -> None:
        setup = {"routes": ROUTES, "src": "nic", "dst": "kernel"}
        self.assertEqual(
            PacketRouteSimulator().run(setup),
            ["nic", "pch", "cpu_package", "kernel"],
        )

    def test_alternate_destination_branches_at_pch(self) -> None:
        setup = {"routes": ROUTES, "src": "nic", "dst": "ssd"}
        self.assertEqual(
            PacketRouteSimulator().run(setup),
            ["nic", "pch", "storage_controller", "ssd"],
        )

    def test_missing_route_raises(self) -> None:
        setup = {"routes": ROUTES, "src": "nic", "dst": "bios"}
        with self.assertRaises(ValueError):
            PacketRouteSimulator().run(setup)

    def test_loop_detection_raises(self) -> None:
        setup = {
            "routes": {"a": {"x": "b"}, "b": {"x": "a"}},
            "src": "a",
            "dst": "x",
        }
        with self.assertRaises(ValueError):
            PacketRouteSimulator().run(setup)


class TestSeekDistance(unittest.TestCase):
    def test_fcfs_total_movement(self) -> None:
        """From track 50, FCFS through 60, 40, 70: 10 + 20 + 30 = 60."""
        setup = {"algorithm": "FCFS", "start_track": 50, "requests": [60, 40, 70]}
        self.assertEqual(SeekDistanceSimulator().run(setup), 60)

    def test_sstf_total_movement(self) -> None:
        """SSTF from 50: nearest is 60 (10), then 70 (10), then 40 (30) = 50."""
        setup = {"algorithm": "SSTF", "start_track": 50, "requests": [60, 40, 70]}
        self.assertEqual(SeekDistanceSimulator().run(setup), 50)

    def test_sstf_never_worse_than_fcfs(self) -> None:
        for requests in ([10, 90, 20, 80], [5, 95, 50], [1, 2, 3]):
            fcfs = SeekDistanceSimulator().run(
                {"algorithm": "FCFS", "start_track": 50, "requests": requests}
            )
            sstf = SeekDistanceSimulator().run(
                {"algorithm": "SSTF", "start_track": 50, "requests": requests}
            )
            self.assertLessEqual(sstf, fcfs, requests)

    def test_unknown_algorithm_raises(self) -> None:
        with self.assertRaises(ValueError):
            SeekDistanceSimulator().run(
                {"algorithm": "SCAN", "start_track": 0, "requests": [1]}
            )


class TestSignatureMatch(unittest.TestCase):
    SIGNATURES = {
        "boot_sector_virus": "XJMP:0x7C00",
        "rootkit_virus": "hide_proc(",
    }

    def test_match_returns_virus_name(self) -> None:
        setup = {
            "signatures": self.SIGNATURES,
            "file_contents": "data data XJMP:0x7C00 more data",
        }
        self.assertEqual(SignatureMatchSimulator().run(setup), "boot_sector_virus")

    def test_no_match_returns_clean(self) -> None:
        setup = {"signatures": self.SIGNATURES, "file_contents": "innocent bytes"}
        self.assertEqual(SignatureMatchSimulator().run(setup), "clean")

    def test_near_miss_does_not_match(self) -> None:
        """Signature matching is exact: a one-character difference is clean.
        That is the whole lesson of the signature puzzle."""
        setup = {"signatures": self.SIGNATURES, "file_contents": "XJMP:0x7C0"}
        self.assertEqual(SignatureMatchSimulator().run(setup), "clean")


if __name__ == "__main__":
    unittest.main()
