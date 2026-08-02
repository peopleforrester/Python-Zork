# ABOUTME: Flash write cost under in-place vs erase-block policy: write amplification.
# ABOUTME: New simulator per contract; storage/seek.py is never edited in place.

"""Educational flash-write simulator.

`storage.py` models a disk head crossing tracks, and every storage puzzle in the
game was built on it, including one that stood in the SSD room asking how far a
head travelled. An SSD has no head. This gives flash its own lesson.

The lesson is write amplification, and it comes from one asymmetry: flash is
written a page at a time but can only be *erased* a whole block at a time, so a
page that already holds data cannot be overwritten where it sits. Rewriting one
page means writing its block's live contents somewhere clean. The drive does far
more writing than the host asked for, which is why an SSD wears out on small
random rewrites and shrugs at sequential ones.

  in_place    = one page written per host write (what a disk can do, flash cannot)
  erase_block = a clean page costs 1; rewriting a used page costs a whole block

Fidelity statement (contract: docs/architecture-microquiz.md): models the cost
in page-writes of a sequence of host page-writes against a flash device with a
fixed block size, under either an in-place policy (the counterfactual, offered
so the amplification is measurable against something) or an erase-block policy
where rewriting an already-written page rewrites its entire block. NOT modeled:
the erase operation's own cost or its asymmetry with programming; a
free-block pool, over-provisioning, or the fact that a real drive copies to a
pre-erased block rather than erasing in the write path; background garbage
collection and when it runs; wear levelling and block lifetime; the FTL's
logical-to-physical map; read-disturb; SLC caching; TRIM; parallelism across
dies, planes or channels; and any notion of time, since the answer counts
page-writes rather than microseconds. The erase-block figure is the pessimistic
bound a drive with no free pages would pay, which is what makes the trade
legible; a real drive amortises much of it.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import (
    MAX_TRACE_LENGTH,
    AnswerKind,
    require_within,
)

POLICIES = ("in_place", "erase_block")


class FlashWriteSimulator:
    """Total page-writes the device performs for a sequence of host writes."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        policy = str(setup.get("policy", "erase_block")).lower()
        if policy not in POLICIES:
            raise ValueError(
                f"unknown policy {policy!r}; expected one of {', '.join(POLICIES)}"
            )

        pages_per_block = int(setup["pages_per_block"])
        if pages_per_block <= 0:
            raise ValueError(f"pages_per_block is {pages_per_block}; expected > 0")

        writes = [int(page) for page in setup["writes"]]
        if not writes:
            raise ValueError("writes is empty; the workload needs at least one write")
        require_within("write count", len(writes), MAX_TRACE_LENGTH)
        for page in writes:
            if page < 0:
                raise ValueError(f"page {page} is negative")

        if policy == "in_place":
            # The counterfactual: the host asked for N writes and got N.
            return len(writes)

        total = 0
        written: set[int] = set()
        for page in writes:
            if page in written:
                # The page holds data, so it cannot be overwritten where it is.
                # Its whole block is rewritten, and the block starts clean again
                # apart from this page.
                block = page // pages_per_block
                total += pages_per_block
                written -= {
                    p for p in written if p // pages_per_block == block
                }
                written.add(page)
            else:
                total += 1
                written.add(page)
        return total
