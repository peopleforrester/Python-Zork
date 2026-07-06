# ABOUTME: Educational virus-signature matcher, exact substring against a list.
# ABOUTME: Backs the security micro-puzzles.

"""Educational virus-signature matching simulator.

Fidelity statement (contract: docs/architecture-microquiz.md): models
exact-pattern matching of file contents against a curated signature
list; the first matching signature (in dictionary order) names the
verdict, and no match is "clean". NOT modeled: heuristic detection,
behavior monitoring, polymorphic-virus dynamic matching, sandbox
emulation. Verdicts say "this matches the canonical signature for X";
they do not say "this is, in the world, a virus."
"""

from __future__ import annotations

from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import AnswerKind


class SignatureMatchSimulator:
    """Name of the first matching signature, or 'clean'."""

    answer_kind: ClassVar[AnswerKind] = AnswerKind.CHOICE

    def run(self, setup: dict[str, Any]) -> str:
        signatures = {str(k): str(v) for k, v in dict(setup["signatures"]).items()}
        contents = str(setup["file_contents"])
        for name, pattern in signatures.items():
            if pattern in contents:
                return name
        return "clean"
