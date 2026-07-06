# ABOUTME: Educational packet-routing simulator over a static next-hop topology.
# ABOUTME: Backs the networking micro-puzzles.

"""Educational network routing simulator.

Fidelity statement (contract: docs/architecture-microquiz.md): models
static next-hop routing over a small named topology, the shape of an IP
forwarding table reduced to component names. NOT modeled: TCP windowing,
congestion control, retransmit, NAT, firewall policy, MTU fragmentation,
IPv6, ARP timing, or any wireless effect. Verdicts assume a quiet,
lossless wire.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import AnswerKind


class PacketRouteSimulator:
    """Hop-by-hop path a packet takes from src to dst."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.SEQUENCE

    def run(self, setup: dict[str, Any]) -> list[str]:
        routes: dict[str, dict[str, str]] = {
            str(node): {str(d): str(n) for d, n in table.items()}
            for node, table in dict(setup["routes"]).items()
        }
        src = str(setup["src"])
        dst = str(setup["dst"])

        path = [src]
        current = src
        # Any legitimate path is bounded by the node count; anything longer
        # is a routing loop in the authored table.
        max_hops = len(routes) + 2
        while current != dst:
            table = routes.get(current)
            if table is None or dst not in table:
                raise ValueError(f"{current} has no route toward {dst}")
            current = table[dst]
            path.append(current)
            if len(path) > max_hops:
                raise ValueError(f"routing loop detected on the way to {dst}")
        return path
