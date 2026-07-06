# ABOUTME: Educational disk-seek simulator, total head movement per algorithm.
# ABOUTME: Backs the storage micro-puzzles.

"""Educational block-storage simulator.

Fidelity statement (contract: docs/architecture-microquiz.md): models a
disk head moving across numbered tracks, and the total seek distance for
a request queue under FCFS or SSTF scheduling. NOT modeled: rotational
latency, transfer time, SCAN and elevator variants, SSD internals
(garbage collection, wear leveling, write amplification), NCQ, or
controller caching. Verdicts cite the textbook HDD seek model.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import AnswerKind

_ALGORITHMS = frozenset({"FCFS", "SSTF"})


class SeekDistanceSimulator:
    """Total track movement to satisfy a request queue."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        algorithm = str(setup["algorithm"]).upper()
        if algorithm not in _ALGORITHMS:
            raise ValueError(f"unknown scheduling algorithm {setup['algorithm']!r}")
        head = int(setup["start_track"])
        pending = [int(t) for t in setup["requests"]]

        total = 0
        if algorithm == "FCFS":
            for track in pending:
                total += abs(head - track)
                head = track
        else:  # SSTF: always service the nearest pending request next.
            while pending:
                nearest = min(pending, key=lambda t: abs(head - t))
                pending.remove(nearest)
                total += abs(head - nearest)
                head = nearest
        return total
