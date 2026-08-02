# ABOUTME: SIMD warp cost under a uniform vs divergent branch: the GPU lesson.
# ABOUTME: Nothing else in the game models parallelism; the GPU room taught nothing.

"""Educational SIMD warp-divergence simulator.

The GPU room describes thousands of cores working simultaneously, and until now
no simulator anywhere in the game modelled parallelism at all. This gives the
room the lesson its own description promises, and it is the one that actually
surprises people: a GPU's lanes do not run independently.

Lanes execute in lockstep groups (a warp). One instruction pointer serves the
whole group, so when a branch sends some lanes one way and some the other, the
hardware cannot run both at once. It runs the `then` side with the disagreeing
lanes masked off, then the `else` side with the others masked off. The warp pays
the SUM of both sides rather than the max, and it pays it if even one lane
disagrees.

That produces the result worth carrying away: identical work, identical lane
count, and merely reordering which lane does which job changes the cost. Sorting
work so that a warp agrees with itself is free performance; scattering it is a
tax the code never mentions.

  uniform warp   = the cost of the side its lanes took
  divergent warp = then_cost + else_cost, regardless of the split

Fidelity statement (contract: docs/architecture-microquiz.md): models the cost
in abstract instruction-slots of one branch executed by a fixed-width warp,
where a warp whose lanes disagree serialises both sides. Lanes are grouped into
warps in order, and a partial final warp behaves like a full one. NOT modelled:
memory coalescing or any memory system at all; occupancy, register pressure and
how many warps a scheduler keeps in flight; latency hiding by switching warps,
which is the main reason a real GPU tolerates stalls; reconvergence points and
the stack that tracks them; independent thread scheduling on architectures that
have it; nested or looping divergence; atomics, barriers and synchronisation;
and any notion of clock time, since the answer counts slots rather than
nanoseconds. The figure is the cost of one branch in isolation, which is what
makes the trade legible; a real kernel overlaps much of it with other warps.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import (
    MAX_TRACE_LENGTH,
    AnswerKind,
    require_within,
)


class WarpDivergenceSimulator:
    """Total instruction-slots a set of lanes costs over one branch."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        lanes = int(setup["lanes"])
        if lanes <= 0:
            raise ValueError(f"lanes is {lanes}; expected > 0")

        then_cost = int(setup["then_cost"])
        else_cost = int(setup["else_cost"])
        for name, cost in (("then_cost", then_cost), ("else_cost", else_cost)):
            if cost < 0:
                raise ValueError(f"{name} is {cost}; expected >= 0")

        taken = [bool(t) for t in setup["taken"]]
        if not taken:
            raise ValueError("taken is empty; the workload needs at least one lane")
        require_within("lane count", len(taken), MAX_TRACE_LENGTH)

        total = 0
        # Lanes fill warps in order, so which lane does which job is exactly
        # what decides whether a warp agrees with itself.
        for start in range(0, len(taken), lanes):
            warp = taken[start:start + lanes]
            if all(warp):
                total += then_cost
            elif not any(warp):
                total += else_cost
            else:
                # One instruction pointer, two destinations: both sides run.
                total += then_cost + else_cost
        return total
