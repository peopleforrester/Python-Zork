# ABOUTME: Loads and validates the YAML puzzle tree; indexes by id and category.
# ABOUTME: evaluate() glues parser + simulator + verify for the command layer.

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from computerquest.mechanics.puzzles.parsers import parse_answer
from computerquest.mechanics.puzzles.types import MicroPuzzle
from computerquest.mechanics.simulators.base import AnswerKind, Verdict, verify_sequence
from computerquest.mechanics.simulators.cache import CacheSimulator
from computerquest.mechanics.simulators.flash import FlashWriteSimulator
from computerquest.mechanics.simulators.interleave import ChannelInterleaveSimulator
from computerquest.mechanics.simulators.link import LinkCostSimulator
from computerquest.mechanics.simulators.packet import PacketRouteSimulator
from computerquest.mechanics.simulators.pipeline import PipelineSimulator
from computerquest.mechanics.simulators.scanner import (
    MultiMatchScanSimulator,
    WildcardScanSimulator,
)
from computerquest.mechanics.simulators.signature import SignatureMatchSimulator
from computerquest.mechanics.simulators.simd import WarpDivergenceSimulator
from computerquest.mechanics.simulators.storage import SeekDistanceSimulator
from computerquest.mechanics.simulators.tlb import TLBSimulator, TLBTranslateSimulator

DATA_ROOT = Path(__file__).parent / "data"

VALID_CATEGORIES = frozenset({"cpu", "memory", "storage", "networking", "security"})

# Named simulator table the contract's registry resolves puzzles against.
SIMULATORS: dict[str, Any] = {
    "cache": CacheSimulator(),
    "pipeline": PipelineSimulator(),
    "tlb": TLBSimulator(),
    "tlb_translate": TLBTranslateSimulator(),
    "packet": PacketRouteSimulator(),
    "seek": SeekDistanceSimulator(),
    "signature": SignatureMatchSimulator(),
    # Added by PRD 1 Feature B. New entries only: editing the two above in
    # place would invalidate the nine puzzles built on their current answers.
    "scan_all": MultiMatchScanSimulator(),
    "scan_wildcard": WildcardScanSimulator(),
    "link_cost": LinkCostSimulator(),
    # Storage taught one lesson (head travel) five times, including in the SSD
    # room, which has no head. storage.py is untouched; this sits beside it.
    "flash": FlashWriteSimulator(),
    # The GPU room described thousands of parallel cores and taught nothing;
    # no simulator modelled parallelism at all.
    "simd": WarpDivergenceSimulator(),
    # The memory controller room taught nothing, while three duplicate DIMM
    # rooms silently raised the question this answers.
    "interleave": ChannelInterleaveSimulator(),
}


class PuzzleDataError(ValueError):
    """A puzzle YAML file is malformed or unplayable. Author error, not player error."""


@dataclass(frozen=True)
class PuzzleRegistry:
    # Indexed by id only. A by_category index was built on every load and read
    # nowhere: rooms bind puzzles by id in architecture.py, and
    # component_category is descriptive, so nothing ever looked a puzzle up by
    # it.
    by_id: dict[str, MicroPuzzle] = field(default_factory=dict)

    @classmethod
    def from_directory(cls, root: Path) -> PuzzleRegistry:
        """Load every *.yaml under root; validate each puzzle is playable.

        Validation is the author gate: unique ids, known category/subject,
        difficulty 1-3, a resolvable simulator, and a setup the simulator
        can actually run to an answer of the declared shape. A tree that
        fails any of these raises PuzzleDataError at load time so a broken
        puzzle can never reach a player.
        """
        by_id: dict[str, MicroPuzzle] = {}

        for path in sorted(root.rglob("*.yaml")):
            puzzle = _parse_file(path)
            if puzzle.id in by_id:
                raise PuzzleDataError(f"{path}: duplicate puzzle id {puzzle.id!r}")
            _validate_playable(puzzle, path)
            by_id[puzzle.id] = puzzle

        return cls(by_id=by_id)

    def canonical_answer(self, puzzle_id: str) -> Any:
        puzzle = self.by_id[puzzle_id]
        return SIMULATORS[puzzle.simulator].run(puzzle.setup)

    def evaluate(self, puzzle_id: str, raw_answer: str) -> Verdict:
        """Parse the player's raw line, run the simulator, diff the two.

        Raises KeyError for an unknown id and AnswerParseError for a
        wrong-shape answer; both are caller concerns (step 4's command
        layer turns them into player-facing messages).
        """
        puzzle = self.by_id[puzzle_id]
        given = parse_answer(puzzle.answer_kind, raw_answer, grammar=puzzle.answer_grammar)
        canonical = self.canonical_answer(puzzle_id)

        if puzzle.answer_kind is AnswerKind.SEQUENCE:
            return verify_sequence([str(g) for g in given], [str(c) for c in canonical])

        if puzzle.answer_kind is AnswerKind.CHOICE:
            # SEQUENCE grades case-insensitively (base._norm), so CHOICE must
            # too, or a correct pick in the wrong case is marked wrong.
            matched = str(given).strip().casefold() == str(canonical).strip().casefold()
        else:
            matched = given == canonical
        return Verdict(
            correct=matched,
            summary="correct" if matched else f"expected {canonical}, got {given}",
        )


def _parse_file(path: Path) -> MicroPuzzle:
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise PuzzleDataError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise PuzzleDataError(f"{path}: expected a mapping at top level")

    try:
        return MicroPuzzle(
            id=str(data["id"]),
            component_category=str(data["component_category"]),
            subject_area=str(data["subject_area"]),
            difficulty=int(data["difficulty"]),
            title=str(data["title"]),
            prompt=str(data["prompt"]),
            simulator=str(data["simulator"]),
            setup=dict(data["setup"]),
            answer_kind=AnswerKind(str(data["answer_kind"])),
            answer_grammar=str(data["answer_grammar"]),
            explanation=str(data["explanation"]),
            hints=tuple(str(h) for h in data.get("hints", [])),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PuzzleDataError(f"{path}: {exc}") from exc


def _validate_playable(puzzle: MicroPuzzle, path: Path) -> None:
    if puzzle.component_category not in VALID_CATEGORIES:
        raise PuzzleDataError(f"{path}: unknown component_category {puzzle.component_category!r}")
    if puzzle.subject_area not in VALID_CATEGORIES:
        raise PuzzleDataError(f"{path}: unknown subject_area {puzzle.subject_area!r}")
    if puzzle.difficulty not in (1, 2, 3):
        raise PuzzleDataError(f"{path}: difficulty must be 1-3, got {puzzle.difficulty}")
    simulator = SIMULATORS.get(puzzle.simulator)
    if simulator is None:
        raise PuzzleDataError(f"{path}: unknown simulator {puzzle.simulator!r}")
    # Validation runs the author's setup, so resource exhaustion is a real
    # outcome here rather than a hypothetical. Those are not data errors and
    # must not be relabelled: MemoryError carries no message, so wrapping it
    # produced the useless "setup is not runnable: " with nothing after the
    # colon, and swallowing it also defeats any watchdog wrapped around load.
    try:
        simulator.run(puzzle.setup)
    except (MemoryError, RecursionError, KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:  # noqa: BLE001 — any author-side failure is a data error
        raise PuzzleDataError(f"{path}: setup is not runnable: {exc}") from exc

    if puzzle.answer_kind is not simulator.answer_kind:
        # A mismatch loads cleanly today and then compares an int against a
        # list forever, so every answer is wrong with no error at any layer.
        raise PuzzleDataError(
            f"{path}: answer_kind {puzzle.answer_kind.value!r} does not match "
            f"simulator {puzzle.simulator!r} which returns "
            f"{simulator.answer_kind.value!r}"
        )


def load_registry() -> PuzzleRegistry:
    """Load the shipped puzzle tree."""
    return PuzzleRegistry.from_directory(DATA_ROOT)
