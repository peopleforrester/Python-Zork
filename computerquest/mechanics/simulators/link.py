# ABOUTME: Transfer cost across a path of links, store-and-forward vs cut-through.
# ABOUTME: The on-theme networking knob; packet.py stays untouched by contract.

"""Educational link-cost simulator.

`packet.py` answers "which way does it go" and has no policy knob. This answers
"what does it cost", and its knob is the switching discipline, which is the
on-theme axis for a game whose networking rooms mostly teach interconnect and
DMA rather than IP.

The lesson deliberately rhymes with the pipeline simulator. Store-and-forward
makes every hop wait for the whole message, so transmission cost multiplies by
hop count. Cut-through starts forwarding as soon as the header is in, so the
hops overlap and the transmission cost is paid once, at the bottleneck. That is
the same k + (n - 1) shape the CPU rooms teach, one layer down.

Fidelity statement (contract: docs/architecture-microquiz.md): models total
transfer time over an ordered path of independent links, each with a fixed
per-hop latency and a fixed bandwidth, for a single message sent once on an
otherwise idle path.

  store_and_forward = sum(latency) + sum(size / bandwidth)
  cut_through       = sum(latency) + max(size / bandwidth)

The cut-through figure is the idealised pipelined bound: the first bit pays
every latency, the last bit pays one transmission at the slowest link. NOT
modeled: header size or per-hop header parsing cost, queueing behind other
traffic, buffering limits, loss and retransmission, congestion control,
acknowledgements, protocol overhead, serialisation of a message into cells, or
the fact that a real cut-through switch must fall back to store-and-forward
when the outgoing link is busy or slower than the incoming one. Times are in
abstract ticks; bandwidth is payload units per tick.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import (
    MAX_LINKS,
    AnswerKind,
    require_within,
)

MODES = ("store_and_forward", "cut_through")


class LinkCostSimulator:
    """Total ticks to move `size` units across `links` under a switching mode."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        mode = str(setup.get("mode", "store_and_forward")).lower()
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}; expected one of {', '.join(MODES)}")

        links = list(setup["links"])
        if not links:
            raise ValueError("links is empty; a path needs at least one hop")
        require_within("link count", len(links), MAX_LINKS)

        size = int(setup["size"])
        if size <= 0:
            raise ValueError(f"size is {size}; expected a positive payload")

        latencies = []
        transmissions = []
        for index, link in enumerate(links):
            bandwidth = int(link["bandwidth"])
            if bandwidth <= 0:
                raise ValueError(f"link {index} has bandwidth {bandwidth}; expected > 0")
            if size % bandwidth:
                # A fractional tick cannot be typed as an answer, and rounding
                # would make the canonical answer depend on a convention the
                # player cannot see. Author error, reported like any other.
                raise ValueError(
                    f"link {index}: size {size} is not divisible by bandwidth "
                    f"{bandwidth}, so the cost is not a whole number of ticks"
                )
            latencies.append(int(link["latency"]))
            transmissions.append(size // bandwidth)

        overlap = sum if mode == "store_and_forward" else max
        return sum(latencies) + overlap(transmissions)
