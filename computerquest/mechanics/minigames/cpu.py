# ABOUTME: CPU pipeline minigame; delegates all timing to simulators.pipeline.
# ABOUTME: The player steps cycle by cycle and toggles pipelining and forwarding.

from __future__ import annotations

from typing import Any

from computerquest.mechanics.minigames._common import Mode
from computerquest.mechanics.minigames.cpu_workload import WORKLOAD, format_instruction
from computerquest.mechanics.simulators.pipeline import (
    PipelineResult,
    PipelineSimulator,
)

_STAGE_NAMES = ("IF", "ID", "EX", "MEM", "WB")


class CPUPipelineMinigame:
    """A steppable view over PipelineSimulator's cycle-accurate timeline.

    The minigame owns no pipeline logic: it asks the simulator for the full
    per-instruction stage timeline once, then walks it a cycle at a time.
    The only thing it computes itself is the non-pipelined mode, which is the
    trivial "each instruction occupies one stage at a time" model (five cycles
    per instruction, no overlap).
    """

    def __init__(self, game: Any) -> None:
        self.game = game
        self.workload = WORKLOAD
        self.pipelined = True
        self.forwarding = False  # default off so stalls show prominently
        self.cycle = 0
        self.mode = Mode.RUNNING
        self._sim = PipelineSimulator()
        self._recompute()

    # --- timeline ---------------------------------------------------------

    def _recompute(self) -> None:
        self.cycle = 0
        self.mode = Mode.RUNNING
        if self.pipelined:
            self._result: PipelineResult = self._sim.simulate(self.workload, self.forwarding)
            self._final = self._result.total_cycles
        else:
            # Non-pipelined: one instruction traverses all five stages before
            # the next issues. Forwarding is irrelevant (no overlap to hazard).
            self._result = self._sim.simulate(self.workload, self.forwarding)
            self._final = len(self.workload) * len(_STAGE_NAMES)

    def total_cycles(self) -> int:
        return self._final

    def is_finished(self) -> bool:
        return self.mode is Mode.FINISHED

    def _stage_occupants(self, cycle: int) -> list[int | None]:
        """Instruction index occupying each of the five stages at `cycle`,
        or None. Pipelined mode reads the simulator's timeline; non-pipelined
        places one instruction in one stage at a time."""
        occ: list[int | None] = [None] * len(_STAGE_NAMES)
        if not self.pipelined:
            if cycle < 1:
                return occ
            slot = (cycle - 1) // len(_STAGE_NAMES)
            stage = (cycle - 1) % len(_STAGE_NAMES)
            if slot < len(self.workload):
                occ[stage] = slot
            return occ
        r = self._result
        for i in range(len(self.workload)):
            if r.if_cycles[i] == cycle:
                occ[0] = i
            elif r.id_entry_cycles[i] <= cycle <= r.id_exit_cycles[i]:
                occ[1] = i
            elif r.ex_cycles[i] == cycle:
                occ[2] = i
            elif r.mem_cycles[i] == cycle:
                occ[3] = i
            elif r.wb_cycles[i] == cycle:
                occ[4] = i
        return occ

    # --- verbs ------------------------------------------------------------

    def step(self) -> str:
        if self.mode is Mode.FINISHED:
            return "The run is finished. Use 'simulate reset' or 'simulate toggle'."
        self.cycle += 1
        if self.cycle >= self._final:
            self.mode = Mode.FINISHED
            return self._render(header=f"Cycle {self.cycle}: last instruction retired.\n") + \
                "\n\n" + self._debrief()
        return self._render()

    def toggle_pipeline(self) -> str:
        self.pipelined = not self.pipelined
        self._recompute()
        which = "pipelined" if self.pipelined else "non-pipelined"
        return f"Switched to {which} mode; workload restarted at cycle 0.\n\n" + self.explain()

    def toggle_forwarding(self) -> str:
        self.forwarding = not self.forwarding
        self._recompute()
        state = "on" if self.forwarding else "off"
        return f"Forwarding {state}; workload restarted at cycle 0.\n\n" + self.explain()

    def reset(self) -> str:
        self._recompute()
        return "Reset to cycle 0 (mode and forwarding kept).\n\n" + self.explain()

    # --- rendering --------------------------------------------------------

    def explain(self) -> str:
        lines = [
            "CPU PIPELINE SIMULATION",
            "Stages: IF (fetch)  ID (decode)  EX (execute)  MEM (memory)  WB (writeback)",
            "",
            "Workload:",
        ]
        for i, inst in enumerate(self.workload):
            lines.append(f"  {i}: {format_instruction(inst)}")
        mode = "pipelined" if self.pipelined else "non-pipelined"
        fwd = "on" if self.forwarding else "off"
        lines.append("")
        lines.append(f"Mode: {mode} | Forwarding: {fwd} | Projected total: {self._final} cycles")
        lines.append("Use 'simulate step' to advance, 'simulate forward' to toggle forwarding,")
        lines.append("'simulate toggle' for non-pipelined, 'simulate stop' to leave.")
        return "\n".join(lines)

    def get_status(self) -> str:
        if self.mode is Mode.FINISHED:
            return self._render() + "\n\n" + self._debrief()
        return self._render()

    def _render(self, header: str = "") -> str:
        occ = self._stage_occupants(self.cycle)
        cells = []
        for name, who in zip(_STAGE_NAMES, occ):
            if who is None:
                body = "--bubble--" if self.cycle > 0 else "  empty   "
            else:
                body = f"i{who}:{self.workload[who].opcode:<7}"
            cells.append(f"{name:>3}[{body}]")
        pipe = "  ".join(cells)
        retired = sum(1 for i in range(len(self.workload)) if self._instruction_done(i))
        thru = retired / self.cycle if self.cycle else 0.0
        return (
            f"{header}Cycle {self.cycle}/{self._final}\n"
            f"{pipe}\n"
            f"Retired: {retired}/{len(self.workload)}  Throughput: {thru:.2f} instr/cycle"
        )

    def _instruction_done(self, i: int) -> bool:
        if self.pipelined:
            return self._result.wb_cycles[i] <= self.cycle
        return (i + 1) * len(_STAGE_NAMES) <= self.cycle

    def _debrief(self) -> str:
        stalls = sum(self._result.stalls_per_instruction) if self.pipelined else 0
        mode = "pipelined" if self.pipelined else "non-pipelined"
        fwd = "on" if self.forwarding else "off"
        thru = len(self.workload) / self._final
        lines = [
            "DEBRIEF",
            f"  Mode: {mode}, forwarding {fwd}",
            f"  Total cycles: {self._final}",
            f"  Instructions: {len(self.workload)}  Throughput: {thru:.2f} instr/cycle",
        ]
        if self.pipelined:
            lines.append(f"  Stall cycles from hazards: {stalls}")
            if not self.forwarding:
                lines.append("  Try 'simulate forward' to forward results and cut the stalls.")
            lines.append("  Try 'simulate toggle' to see the non-pipelined timeline for contrast.")
        else:
            lines.append("  Non-pipelined pays five cycles per instruction, no overlap.")
            lines.append("  Try 'simulate toggle' to pipeline it and watch the total drop.")
        return "\n".join(lines)
