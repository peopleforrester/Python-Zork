#!/usr/bin/env python3
"""
ABOUTME: Tests for AnswerKind input parsers — tolerant of separators, strict on shape.
ABOUTME: Wrong shape raises AnswerParseError carrying the puzzle's answer grammar.
"""

import unittest

from computerquest.mechanics.puzzles.parsers import AnswerParseError, parse_answer
from computerquest.mechanics.simulators.base import AnswerKind


class TestSequenceParser(unittest.TestCase):
    def test_whitespace_separated(self) -> None:
        self.assertEqual(parse_answer(AnswerKind.SEQUENCE, "H M M H"), ["H", "M", "M", "H"])

    def test_commas_and_mixed_case_tolerated(self) -> None:
        self.assertEqual(parse_answer(AnswerKind.SEQUENCE, "h, m,,  H"), ["h", "m", "H"])

    def test_empty_raises(self) -> None:
        with self.assertRaises(AnswerParseError):
            parse_answer(AnswerKind.SEQUENCE, "   ")


class TestNumberParser(unittest.TestCase):
    def test_plain_int(self) -> None:
        self.assertEqual(parse_answer(AnswerKind.NUMBER, " 42 "), 42)

    def test_non_numeric_raises_with_grammar(self) -> None:
        with self.assertRaises(AnswerParseError) as ctx:
            parse_answer(AnswerKind.NUMBER, "eleven", grammar="a single whole number")
        self.assertIn("a single whole number", str(ctx.exception))


class TestBoolParser(unittest.TestCase):
    def test_truthy_variants(self) -> None:
        for token in ("y", "yes", "true", "TRUE"):
            self.assertIs(parse_answer(AnswerKind.BOOL, token), True)

    def test_falsy_variants(self) -> None:
        for token in ("n", "no", "false", "No"):
            self.assertIs(parse_answer(AnswerKind.BOOL, token), False)

    def test_garbage_raises(self) -> None:
        with self.assertRaises(AnswerParseError):
            parse_answer(AnswerKind.BOOL, "maybe")


class TestChoiceParser(unittest.TestCase):
    def test_single_token(self) -> None:
        self.assertEqual(parse_answer(AnswerKind.CHOICE, " stall "), "stall")

    def test_multiple_tokens_raise(self) -> None:
        with self.assertRaises(AnswerParseError):
            parse_answer(AnswerKind.CHOICE, "stall forward")


class TestMappingParser(unittest.TestCase):
    def test_key_value_pairs(self) -> None:
        self.assertEqual(
            parse_answer(AnswerKind.MAPPING, "n=core1 s=l3_cache"),
            {"n": "core1", "s": "l3_cache"},
        )

    def test_missing_equals_raises(self) -> None:
        with self.assertRaises(AnswerParseError):
            parse_answer(AnswerKind.MAPPING, "n core1")


if __name__ == "__main__":
    unittest.main()
