# ABOUTME: Educational cache simulator — hit/miss prediction for micro-puzzles.
# ABOUTME: Also the state engine for the memory-hierarchy minigame (Step 7).

"""Educational cache simulator.

Fidelity statement (contract: docs/architecture-microquiz.md): models
direct-mapped and set-associative caches with configurable line size,
associativity, and replacement policy (LRU and FIFO). Lines are addressed
by tag and index; valid bits are tracked. NOT modeled: MESI or any other
coherence protocol; hardware prefetching; write buffers; multi-level
inclusion or exclusion; non-power-of-two behavior beyond what integer
division gives; trace-driven warmup. Verdicts assume a cold cache at the
start of each puzzle.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import AnswerKind

_POLICIES = frozenset({"LRU", "FIFO"})


class CacheSimulator:
    """Pure hit/miss simulation. Same setup, same answer, every time."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.SEQUENCE

    def run(self, setup: dict[str, Any]) -> list[str]:
        """Return the canonical H/M sequence for the setup's access trace.

        Setup schema:
            policy: "LRU" | "FIFO"
            size_lines: total number of cache lines
            line_size_bytes: bytes per line
            associativity: ways per set (1 = direct-mapped;
                           == size_lines = fully associative)
            accesses: list of byte addresses
        """
        policy = str(setup["policy"]).upper()
        if policy not in _POLICIES:
            raise ValueError(f"unknown replacement policy {setup['policy']!r}")

        size_lines = int(setup["size_lines"])
        line_size = int(setup["line_size_bytes"])
        associativity = int(setup["associativity"])
        accesses = list(setup["accesses"])

        if size_lines <= 0 or line_size <= 0 or associativity <= 0:
            raise ValueError("size_lines, line_size_bytes, associativity must be positive")
        if size_lines % associativity != 0:
            raise ValueError(
                f"associativity {associativity} does not divide size_lines {size_lines}"
            )

        num_sets = size_lines // associativity
        # Each set is an ordered list of tags. Position encodes the policy's
        # eviction order: index 0 is always the next victim. LRU refreshes a
        # hit tag to the back; FIFO leaves hit order untouched.
        sets: list[list[int]] = [[] for _ in range(num_sets)]

        result: list[str] = []
        for address in accesses:
            line_number = int(address) // line_size
            index = line_number % num_sets
            tag = line_number // num_sets
            tags = sets[index]

            if tag in tags:
                result.append("H")
                if policy == "LRU":
                    tags.remove(tag)
                    tags.append(tag)
            else:
                result.append("M")
                if len(tags) >= associativity:
                    tags.pop(0)
                tags.append(tag)

        return result
