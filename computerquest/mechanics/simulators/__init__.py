# ABOUTME: Simulator library for predict-and-verify puzzles and minigames.
# ABOUTME: Pure functions from setup dicts to canonical answers; no Game deps.

from computerquest.mechanics.simulators.base import (
    AnswerKind,
    PositionVerdict,
    Verdict,
    verify_sequence,
)
from computerquest.mechanics.simulators.cache import CacheSimulator
from computerquest.mechanics.simulators.pipeline import Instruction, PipelineSimulator

__all__ = [
    "AnswerKind",
    "CacheSimulator",
    "Instruction",
    "PipelineSimulator",
    "PositionVerdict",
    "Verdict",
    "verify_sequence",
]
