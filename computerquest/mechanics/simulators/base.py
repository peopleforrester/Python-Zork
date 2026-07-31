# ABOUTME: Shared simulator types — AnswerKind, Verdict, generic verify helpers.
# ABOUTME: Contract: docs/architecture-microquiz.md (per-simulator fidelity section).

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Protocol

# Upper bounds on author-supplied setup values.
#
# The registry validates a puzzle by *running* it, so any unbounded quantity in
# a setup is executed at load time. One integer was enough to make the cache
# simulator allocate until the OOM killer intervened, and SSTF is quadratic, so
# a long request list is a wall-clock hang with no memory signature.
#
# The shipped tree's largest values are size_lines 4, line_size_bytes 64,
# accesses 10, requests 4, instructions 4, tlb_entries 2, so these sit three to
# four orders of magnitude above any real puzzle and constrain only inputs that
# could not teach anything.
MAX_TRACE_LENGTH = 4096      # accesses, requests, instructions, page-table rows
MAX_CACHE_LINES = 65536
MAX_LINE_SIZE_BYTES = 1 << 20
MAX_TLB_ENTRIES = 65536
MAX_PAGE_SIZE = 1 << 30


def require_within(name: str, value: int, limit: int) -> int:
    """Reject a setup value above `limit`, naming the offender.

    Raises ValueError so the registry reports it as a puzzle data error rather
    than a crash, which is how every other authoring mistake surfaces.
    """
    if value > limit:
        raise ValueError(f"{name} is {value}, above the maximum of {limit}")
    return value


class AnswerKind(str, Enum):
    """Shape of the answer a player commits for a puzzle."""

    CHOICE = "choice"
    SEQUENCE = "sequence"
    NUMBER = "number"
    BOOL = "bool"
    MAPPING = "mapping"


@dataclass(frozen=True)
class PositionVerdict:
    """Per-element correctness for sequence-shaped answers."""

    index: int
    given: str
    expected: str
    matched: bool


@dataclass(frozen=True)
class Verdict:
    """Structured result of comparing a player answer to the canonical one."""

    correct: bool
    positions: list[PositionVerdict] = field(default_factory=list)
    summary: str = ""
    deep_notes: list[str] = field(default_factory=list)


class Simulator(Protocol):
    """A category-specific simulator: pure function from setup to answer."""

    answer_kind: ClassVar[AnswerKind]

    def run(self, setup: dict[str, Any]) -> Any:
        """Return the canonical answer in the shape answer_kind dictates."""
        ...


def _norm(token: str) -> str:
    return token.strip().upper()


def verify_sequence(given: list[str], expected: list[str]) -> Verdict:
    """Element-wise diff of a player's sequence answer against the canonical one.

    Comparison is case- and surrounding-whitespace-insensitive. A length
    mismatch is an incorrect answer with an explanatory summary, never an
    exception — the parser upstream guards shape, but a defensive verdict
    keeps the game loop unconditionally safe.
    """
    if len(given) != len(expected):
        return Verdict(
            correct=False,
            positions=[],
            summary=f"answer has {len(given)} tokens, expected {len(expected)}",
        )

    positions = [
        PositionVerdict(
            index=i,
            given=g.strip(),
            expected=e.strip(),
            matched=_norm(g) == _norm(e),
        )
        for i, (g, e) in enumerate(zip(given, expected))
    ]
    matches = sum(1 for p in positions if p.matched)
    return Verdict(
        correct=matches == len(positions),
        positions=positions,
        summary=f"{matches} of {len(positions)} correct",
    )
