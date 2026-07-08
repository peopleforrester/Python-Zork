#!/usr/bin/env python3
"""
ABOUTME: Tests for the educational 5-stage pipeline simulator (cycle counts).
ABOUTME: Semantics: in-order MIPS-style pipeline per the module fidelity statement.

Timing conventions the expectations are derived from (also documented in
the simulator docstring):
- Without forwarding, a consumer leaves ID in the producer's WB cycle at
  the earliest (write-through register file).
- With forwarding, an ALU result is available after the producer's EX; a
  LOAD result only after its MEM (one unavoidable load-use bubble).
"""

import unittest

from computerquest.mechanics.simulators.pipeline import Instruction, PipelineSimulator

# The cpu_workload chain from the architecture doc: a load feeding an ALU op
# feeding a store. RAW hazards on R2 and R4.
HAZARD_CHAIN = [
    Instruction("LOAD", ("R1",), "R2"),
    Instruction("ADD", ("R2", "R3"), "R4"),
    Instruction("STORE", ("R4", "R1"), None),
]

# Three independent instructions: no hazards anywhere.
NO_HAZARD = [
    Instruction("ADD", ("R1", "R2"), "R3"),
    Instruction("ADD", ("R4", "R5"), "R6"),
    Instruction("ADD", ("R7", "R8"), "R9"),
]


def run_cycles(instructions: list[Instruction], forwarding: bool) -> int:
    result = PipelineSimulator().run(
        {"stages": 5, "forwarding": forwarding, "instructions": instructions}
    )
    assert isinstance(result, int)
    return result


class TestNoHazards(unittest.TestCase):
    def test_ideal_pipeline_fill_plus_drain(self) -> None:
        """k stages + (n-1) instructions: 5 + 2 = 7 cycles."""
        self.assertEqual(run_cycles(NO_HAZARD, forwarding=False), 7)
        self.assertEqual(run_cycles(NO_HAZARD, forwarding=True), 7)

    def test_single_instruction_takes_stage_count(self) -> None:
        one = [Instruction("ADD", ("R1", "R2"), "R3")]
        self.assertEqual(run_cycles(one, forwarding=False), 5)


class TestRawHazards(unittest.TestCase):
    """Hand-derived timelines for the LOAD -> ADD -> STORE chain.

    Forwarding on:
      LOAD : IF1 ID2 EX3 M4 W5
      ADD  : IF2 ID3-4 EX5 M6 W7      (load-use: one bubble; R2 after M4)
      STORE: IF3 ID5 EX6 M7 W8        (R4 forwarded from ADD's EX5)
      total 8

    Forwarding off:
      LOAD : IF1 ID2 EX3 M4 W5
      ADD  : IF2 ID3-5 EX6 M7 W8      (R2 readable in LOAD's W5)
      STORE: IF3 ID6-8 EX9 M10 W11    (R4 readable in ADD's W8)
      total 11
    """

    def test_chain_with_forwarding(self) -> None:
        self.assertEqual(run_cycles(HAZARD_CHAIN, forwarding=True), 8)

    def test_chain_without_forwarding(self) -> None:
        self.assertEqual(run_cycles(HAZARD_CHAIN, forwarding=False), 11)

    def test_forwarding_never_slower(self) -> None:
        for workload in (HAZARD_CHAIN, NO_HAZARD):
            self.assertLessEqual(
                run_cycles(workload, forwarding=True),
                run_cycles(workload, forwarding=False),
            )


class TestTimeline(unittest.TestCase):
    def test_simulate_exposes_per_instruction_stall_counts(self) -> None:
        """The richer simulate() surface feeds the minigame later: it must
        report stalls per instruction, not just the total."""
        sim = PipelineSimulator()
        detail = sim.simulate(HAZARD_CHAIN, forwarding=True)
        self.assertEqual(detail.total_cycles, 8)
        self.assertEqual(len(detail.stalls_per_instruction), len(HAZARD_CHAIN))
        self.assertEqual(sum(detail.stalls_per_instruction), 1)  # the load-use bubble


class TestValidation(unittest.TestCase):
    def test_empty_workload_is_zero_cycles(self) -> None:
        self.assertEqual(run_cycles([], forwarding=True), 0)

    def test_only_five_stage_pipeline_supported(self) -> None:
        with self.assertRaises(ValueError):
            PipelineSimulator().run(
                {"stages": 7, "forwarding": True, "instructions": NO_HAZARD}
            )


if __name__ == "__main__":
    unittest.main()


class TestTimelineFields(unittest.TestCase):
    """simulate() exposes the full per-instruction stage timeline for the
    CPU minigame's Gantt rendering, without the minigame recomputing it."""

    def test_timeline_is_internally_consistent(self) -> None:
        sim = PipelineSimulator()
        r = sim.simulate(HAZARD_CHAIN, forwarding=False)
        n = len(HAZARD_CHAIN)
        for lst in (r.if_cycles, r.id_entry_cycles, r.id_exit_cycles, r.mem_cycles, r.wb_cycles):
            self.assertEqual(len(lst), n)
        for i in range(n):
            self.assertLess(r.if_cycles[i], r.id_entry_cycles[i])
            self.assertLessEqual(r.id_entry_cycles[i], r.id_exit_cycles[i])
            self.assertEqual(r.id_exit_cycles[i] + 1, r.ex_cycles[i])
            self.assertEqual(r.ex_cycles[i] + 1, r.mem_cycles[i])
            self.assertEqual(r.mem_cycles[i] + 1, r.wb_cycles[i])
        self.assertEqual(r.wb_cycles[-1], r.total_cycles)
