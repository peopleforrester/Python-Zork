# ABOUTME: Shared simulator types — AnswerKind, Verdict, generic verify helpers.
# ABOUTME: Contract: docs/architecture-microquiz.md (per-simulator fidelity section).

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Protocol


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
