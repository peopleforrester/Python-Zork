# ABOUTME: Educational TLB simulator, hit/miss prediction and address translation.
# ABOUTME: Backs the virtual-memory micro-puzzles (memory category).

"""Educational virtual-to-physical translation simulator.

Fidelity statement (contract: docs/architecture-microquiz.md): models a
single-level page table with fixed-size pages and a fully-associative TLB
with configurable size and replacement policy (LRU and FIFO). Translation
walks the page table on a miss; the TLB caches the VPN. NOT modeled:
multi-level page tables; huge or transparent huge pages; TLB shootdown
across cores; ASIDs or process tagging; PCID; page faults (an unmapped
VPN is an authoring error, not a simulated fault). Verdicts cite the
textbook x86 paging model.
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import AnswerKind

_POLICIES = frozenset({"LRU", "FIFO"})


def _split(vaddr: int, page_size: int) -> tuple[int, int]:
    return vaddr // page_size, vaddr % page_size


class TLBSimulator:
    """Hit/miss sequence for a virtual-address trace through the TLB."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.SEQUENCE

    def run(self, setup: dict[str, Any]) -> list[str]:
        page_size = int(setup["page_size"])
        entries = int(setup["tlb_entries"])
        policy = str(setup["policy"]).upper()
        if policy not in _POLICIES:
            raise ValueError(f"unknown replacement policy {setup['policy']!r}")
        page_table = {int(k): int(v) for k, v in dict(setup["page_table"]).items()}

        # Ordered VPN list; index 0 is the next victim. LRU refreshes hits
        # to the back; FIFO leaves insertion order untouched.
        tlb: list[int] = []
        result: list[str] = []
        for vaddr in setup["accesses"]:
            vpn, _ = _split(int(vaddr), page_size)
            if vpn not in page_table:
                raise ValueError(f"VPN {vpn} not present in the page table")
            if vpn in tlb:
                result.append("H")
                if policy == "LRU":
                    tlb.remove(vpn)
                    tlb.append(vpn)
            else:
                result.append("M")
                if len(tlb) >= entries:
                    tlb.pop(0)
                tlb.append(vpn)
        return result


class TLBTranslateSimulator:
    """Physical address for one virtual address (the page-walk puzzle)."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.NUMBER

    def run(self, setup: dict[str, Any]) -> int:
        page_size = int(setup["page_size"])
        page_table = {int(k): int(v) for k, v in dict(setup["page_table"]).items()}
        vpn, offset = _split(int(setup["vaddr"]), page_size)
        if vpn not in page_table:
            raise ValueError(f"VPN {vpn} not present in the page table")
        return page_table[vpn] * page_size + offset
