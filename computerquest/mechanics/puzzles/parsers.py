# ABOUTME: Player-input parsers per AnswerKind — tolerant separators, strict shape.
# ABOUTME: Shape errors raise AnswerParseError carrying the puzzle's answer grammar.

from __future__ import annotations

import re
from typing import Any

from computerquest.mechanics.simulators.base import AnswerKind

_TRUTHY = frozenset({"y", "yes", "true"})
_FALSY = frozenset({"n", "no", "false"})
_SPLIT = re.compile(r"[,\s]+")


class AnswerParseError(ValueError):
    """Player input does not have the shape the puzzle expects.

    The message is player-facing: the command layer prints it verbatim, so
    it should read as 'I need an answer like: <grammar>'.
    """


def _fail(grammar: str | None) -> AnswerParseError:
    if grammar:
        return AnswerParseError(f"I need an answer like: {grammar}")
    return AnswerParseError("that answer is not in the shape this puzzle expects")


def parse_answer(kind: AnswerKind, raw: str, grammar: str | None = None) -> Any:
    """Turn a raw player line into the canonical shape for `kind`.

    Tolerates commas, repeated separators, surrounding whitespace, and case
    (for BOOL). Anything shape-ambiguous raises AnswerParseError rather than
    guessing — a wrong-shape answer must never be graded as a wrong answer.
    """
    text = raw.strip()
    if not text:
        raise _fail(grammar)

    if kind is AnswerKind.SEQUENCE:
        return [token for token in _SPLIT.split(text) if token]

    if kind is AnswerKind.NUMBER:
        try:
            # base 0 accepts plain decimal and 0x-prefixed hex, so address
            # answers can be given either way.
            return int(text, 0)
        except ValueError:
            raise _fail(grammar) from None

    if kind is AnswerKind.BOOL:
        lowered = text.lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
        raise _fail(grammar)

    if kind is AnswerKind.CHOICE:
        tokens = [token for token in _SPLIT.split(text) if token]
        if len(tokens) != 1:
            raise _fail(grammar)
        return tokens[0]

    if kind is AnswerKind.MAPPING:
        mapping: dict[str, str] = {}
        for token in (t for t in _SPLIT.split(text) if t):
            key, sep, value = token.partition("=")
            if not sep or not key or not value:
                raise _fail(grammar)
            mapping[key] = value
        return mapping

    raise _fail(grammar)
