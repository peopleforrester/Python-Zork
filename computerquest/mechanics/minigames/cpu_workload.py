# ABOUTME: The canned instruction trace the CPU pipeline minigame runs.
# ABOUTME: Kept separate so the workload can be edited without touching mechanics.

from computerquest.mechanics.simulators.pipeline import Instruction

# Two designed data hazards so the player has to confront stall-vs-forward:
# R2 (load-use) between insts 0 and 1, and R4/R7 through insts 1-3-4. The
# final ADD is hazard-free so clean issue/retire is visible after the drama.
WORKLOAD: list[Instruction] = [
    Instruction("LOAD", ("R1",), "R2"),
    Instruction("ADD", ("R2", "R3"), "R4"),
    Instruction("LOAD", ("R5",), "R6"),
    Instruction("MUL", ("R4", "R6"), "R7"),
    Instruction("STORE", ("R7", "R1"), None),
    Instruction("ADD", ("R8", "R9"), "R10"),
]


def format_instruction(inst: Instruction) -> str:
    """Human-readable one-liner, e.g. 'ADD R4 <- R2, R3'."""
    srcs = ", ".join(inst.sources)
    dest = inst.dest if inst.dest is not None else "(mem)"
    return f"{inst.opcode:<6} {dest} <- {srcs}"
