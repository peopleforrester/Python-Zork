# ABOUTME: Educational 5-stage CPU pipeline simulator — cycle counts + stalls.
# ABOUTME: Also the state engine for the CPU-pipeline minigame (Step 7).

"""Educational 5-stage CPU pipeline simulator (IF, ID, EX, MEM, WB).

Fidelity statement (contract: docs/architecture-microquiz.md): models
in-order issue and RAW data hazards with configurable stall-or-forward
resolution. NOT modeled: branch prediction, speculative execution,
out-of-order execution, register renaming, superscalar issue, control
hazards from real branches (every workload is straight-line code), or
any hazard beyond RAW. Verdicts cite the textbook MIPS pipeline
(Patterson & Hennessy).

Timing conventions (the source of every cycle-count verdict):
- One instruction enters IF per cycle, in order, when IF is free.
- Without forwarding, a consumer may leave ID in the producer's WB cycle
  at the earliest (write-through register file: written and read in the
  same cycle).
- With forwarding, an ALU result is available to a consumer's EX in the
  cycle after the producer's EX; a LOAD result only in the cycle after
  its MEM — the one unavoidable load-use bubble.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import AnswerKind

_STAGES = 5  # IF, ID, EX, MEM, WB


@dataclass(frozen=True)
class Instruction:
    """One straight-line instruction: opcode, source registers, dest register."""

    opcode: str
    sources: tuple[str, ...]
    dest: str | None


@dataclass(frozen=True)
class PipelineResult:
    """Cycle-accurate outcome of one workload run."""

    total_cycles: int
    stalls_per_instruction: list[int]
    # ex_cycle[i] is the cycle instruction i occupied EX; feeds the minigame's
    # Gantt rendering later.
    ex_cycles: list[int] = field(default_factory=list)
    # Full per-instruction stage timeline, so the CPU minigame can render a
    # cycle-by-cycle Gantt without reimplementing hazard logic. All 1-indexed
    # cycle numbers. ID spans id_entry_cycles[i]..id_exit_cycles[i] inclusive.
    if_cycles: list[int] = field(default_factory=list)
    id_entry_cycles: list[int] = field(default_factory=list)
    id_exit_cycles: list[int] = field(default_factory=list)
    mem_cycles: list[int] = field(default_factory=list)
    wb_cycles: list[int] = field(default_factory=list)


class PipelineSimulator:
    """Pure cycle simulation. Same setup, same answer, every time."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        """Return total cycles to retire the setup's workload.

        Setup schema:
            stages: must be 5 (the only supported pipeline shape)
            forwarding: bool
            instructions: list of Instruction (or (opcode, sources, dest)
                          triples, coerced)
        """
        if int(setup["stages"]) != _STAGES:
            raise ValueError(f"only {_STAGES}-stage pipelines are modeled")
        instructions = [
            i if isinstance(i, Instruction) else Instruction(i[0], tuple(i[1]), i[2])
            for i in setup["instructions"]
        ]
        return self.simulate(instructions, bool(setup["forwarding"])).total_cycles

    def simulate(self, instructions: list[Instruction], forwarding: bool) -> PipelineResult:
        """Full per-instruction timing; run() returns just the cycle total."""
        if not instructions:
            return PipelineResult(total_cycles=0, stalls_per_instruction=[])

        # For each instruction compute the cycle it occupies each stage.
        # ID can be prolonged by RAW stalls; every later stage follows the
        # previous one by exactly one cycle (no structural stalls besides
        # the in-order ID back-pressure on the follower's IF).
        ex_cycle: list[int] = []
        mem_cycle: list[int] = []
        wb_cycle: list[int] = []
        stalls: list[int] = []
        id_exit: list[int] = []  # last cycle instruction i sits in ID
        if_cycle: list[int] = []
        id_entry_cycle: list[int] = []

        # dest register -> index of the most recent producer.
        last_writer: dict[str, int] = {}

        for i, inst in enumerate(instructions):
            fetch = i + 1 if i == 0 else max(i + 1, id_exit[i - 1])
            # Earliest ID entry: cycle after IF, and after the predecessor
            # has vacated ID.
            id_entry = fetch + 1 if i == 0 else max(fetch + 1, id_exit[i - 1] + 1)
            if_cycle.append(fetch)
            id_entry_cycle.append(id_entry)

            # RAW constraint: earliest cycle this instruction may enter EX.
            earliest_ex = id_entry + 1
            for src in inst.sources:
                producer = last_writer.get(src)
                if producer is None:
                    continue
                if forwarding:
                    if instructions[producer].opcode == "LOAD":
                        # Load value exists after producer MEM.
                        earliest_ex = max(earliest_ex, mem_cycle[producer] + 1)
                    else:
                        # ALU result forwards out of EX.
                        earliest_ex = max(earliest_ex, ex_cycle[producer] + 1)
                else:
                    # Write-through register file: readable in ID during the
                    # producer's WB cycle, so EX may start the cycle after.
                    earliest_ex = max(earliest_ex, wb_cycle[producer] + 1)

            ex = earliest_ex
            id_exit.append(ex - 1)
            ex_cycle.append(ex)
            mem_cycle.append(ex + 1)
            wb_cycle.append(ex + 2)
            stalls.append((ex - 1) - id_entry)  # cycles spent in ID beyond the first

            if inst.dest is not None:
                last_writer[inst.dest] = i

        return PipelineResult(
            total_cycles=wb_cycle[-1],
            stalls_per_instruction=stalls,
            ex_cycles=ex_cycle,
            if_cycles=if_cycle,
            id_entry_cycles=id_entry_cycle,
            id_exit_cycles=id_exit,
            mem_cycles=mem_cycle,
            wb_cycles=wb_cycle,
        )
