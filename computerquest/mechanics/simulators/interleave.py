# ABOUTME: Memory-channel cost under block vs interleaved address mapping.
# ABOUTME: Answers why a system ships four DIMMs rather than one large one.

"""Educational memory-channel interleaving simulator.

The memory controller room manages every transfer between the CPU and RAM and
taught nothing, while three otherwise-identical DIMM rooms silently raised the
question this answers: why four modules instead of one big one?

Because channels work in parallel, and whether a program gets that parallelism
is decided by how physical addresses are assigned to channels.

Under a **block** mapping each channel owns a contiguous range, so a program
walking sequentially through memory stays inside one channel and the other three
sit idle. Under an **interleaved** mapping consecutive cache lines round-robin
across channels, so the same walk spreads over all four and they serve it at
once. Same hardware, same request stream, four times the throughput, decided by
an address-bit choice the program cannot see.

The catch is worth as much as the lesson: interleaving helps a stride of one and
does nothing for a stride that happens to match the channel count, because every
access then lands on the same channel again. Which is why a matrix walked down
its columns can run several times slower than the same matrix walked along its
rows, with no change to the instruction count.

  cost = cycles taken by the busiest channel, since channels run in parallel

Fidelity statement (contract: docs/architecture-microquiz.md): models the cost
in cycles of one burst of cache-line requests spread across a fixed number of
equal, independent channels, under either a block or a line-interleaved address
mapping, where the answer is the load on the busiest channel because the
channels proceed simultaneously. NOT modelled: DRAM timing of any kind (row
activation, precharge, tRCD/tCAS/tRP, refresh), bank and rank structure within
a channel and the bank-level parallelism they provide, open-row hit and miss
behaviour, read/write turnaround, request reordering by the controller
scheduler, queueing, the cache hierarchy in front of it, prefetching, ECC, and
any asymmetry between channels of different capacity. Cycles are abstract, and
a real controller's scheduler recovers some of the loss a naive block mapping
implies.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import (
    MAX_TRACE_LENGTH,
    AnswerKind,
    require_within,
)

MAPPINGS = ("block", "interleaved")


class ChannelInterleaveSimulator:
    """Cycles for a burst of line requests, set by the busiest channel."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        mapping = str(setup.get("mapping", "interleaved")).lower()
        if mapping not in MAPPINGS:
            raise ValueError(
                f"unknown mapping {mapping!r}; expected one of {', '.join(MAPPINGS)}"
            )

        channels = int(setup["channels"])
        if channels <= 0:
            raise ValueError(f"channels is {channels}; expected > 0")

        width = int(setup.get("lines_per_channel_cycle", 1))
        if width <= 0:
            raise ValueError(f"lines_per_channel_cycle is {width}; expected > 0")

        lines = [int(line) for line in setup["lines"]]
        if not lines:
            raise ValueError("lines is empty; the burst needs at least one request")
        require_within("burst length", len(lines), MAX_TRACE_LENGTH)

        if mapping == "block":
            block_lines = int(setup.get("block_lines", 0))
            if block_lines <= 0:
                raise ValueError(
                    "block mapping needs block_lines, the number of lines each "
                    "channel owns before the next channel begins"
                )

        load = [0] * channels
        for line in lines:
            if mapping == "interleaved":
                # Consecutive lines walk across the channels.
                channel = line % channels
            else:
                # Each channel owns a contiguous run of lines.
                channel = (line // block_lines) % channels
            load[channel] += 1

        # Channels run at the same time, so the burst finishes when the one
        # with the most work does. A partial cycle still costs a whole cycle.
        return max((count + width - 1) // width for count in load)
