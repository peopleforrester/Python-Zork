# ABOUTME: Micro-puzzle infrastructure — types, parsers, YAML registry.
# ABOUTME: Contract: docs/architecture-microquiz.md (sha256:591ed2838167).

from computerquest.mechanics.puzzles.parsers import AnswerParseError, parse_answer
from computerquest.mechanics.puzzles.registry import (
    PuzzleDataError,
    PuzzleRegistry,
    load_registry,
)
from computerquest.mechanics.puzzles.session import HintMode, PuzzleSession
from computerquest.mechanics.puzzles.types import MicroPuzzle

__all__ = [
    "AnswerParseError",
    "HintMode",
    "MicroPuzzle",
    "PuzzleDataError",
    "PuzzleRegistry",
    "PuzzleSession",
    "load_registry",
    "parse_answer",
]
