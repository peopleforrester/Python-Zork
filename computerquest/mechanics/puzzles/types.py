# ABOUTME: MicroPuzzle dataclass — the data shape every puzzle YAML deserializes to.
# ABOUTME: Contract: docs/architecture-microquiz.md (sha256:cde83dbaa90b).

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from computerquest.mechanics.simulators.base import AnswerKind


@dataclass(frozen=True)
class MicroPuzzle:
    """One predict-and-verify puzzle. Authored as YAML, validated at load.

    `simulator` names the entry in the registry's simulator table that
    verifies this puzzle — the contract's registry "resolves the named
    simulator" through this field. `hints` is ordered cheap-to-expensive;
    per decision 3 the first is free and later ones mark the puzzle
    attempted.
    """

    id: str
    component_category: str
    subject_area: str
    difficulty: int
    title: str
    prompt: str
    simulator: str
    setup: dict[str, Any]
    answer_kind: AnswerKind
    answer_grammar: str
    explanation: str
    hints: tuple[str, ...] = field(default=())

    def knowledge_weight(self) -> float:
        """Contribution to the subject-area knowledge meter (decision 5)."""
        return self.difficulty * 0.5 + 0.5
