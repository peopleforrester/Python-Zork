#!/usr/bin/env python3
"""
ABOUTME: Tests for the puzzle registry — YAML loading, indexing, evaluate().
ABOUTME: The registry glues parser + simulator + verify into one call for step 4.
"""

import textwrap
import unittest
from pathlib import Path

from computerquest.mechanics.puzzles.registry import (
    PuzzleDataError,
    PuzzleRegistry,
    load_registry,
)


class TestShippedRegistry(unittest.TestCase):
    """The registry loaded from the packaged data tree."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_doc_example_puzzle_is_present(self) -> None:
        puzzle = self.registry.by_id["l1_lru_basic"]
        self.assertEqual(puzzle.component_category, "memory")
        self.assertEqual(puzzle.difficulty, 1)
        self.assertEqual(puzzle.simulator, "cache")
        self.assertTrue(puzzle.hints)  # decision 3: hints ship as an ordered list

    def test_category_index_covers_all_puzzles(self) -> None:
        total = sum(len(v) for v in self.registry.by_category.values())
        self.assertEqual(total, len(self.registry.by_id))

    def test_evaluate_correct_answer(self) -> None:
        verdict = self.registry.evaluate("l1_lru_basic", "M M M M H M H")
        self.assertTrue(verdict.correct)

    def test_evaluate_wrong_answer_gives_position_feedback(self) -> None:
        verdict = self.registry.evaluate("l1_lru_basic", "M M M M H H H")
        self.assertFalse(verdict.correct)
        mismatches = [p for p in verdict.positions if not p.matched]
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0].index, 5)

    def test_evaluate_number_puzzle(self) -> None:
        self.assertTrue(self.registry.evaluate("pipeline_forwarding_intro", "8").correct)
        self.assertFalse(self.registry.evaluate("pipeline_forwarding_intro", "7").correct)

    def test_unknown_puzzle_id_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.registry.evaluate("does_not_exist", "H")


class TestRegistryValidation(unittest.TestCase):
    """Author-error detection when loading a data tree."""

    def _write(self, root: Path, relpath: str, body: str) -> None:
        target = root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(body))

    def _minimal_puzzle(self, puzzle_id: str) -> str:
        return f"""
            id: {puzzle_id}
            component_category: memory
            subject_area: memory
            difficulty: 1
            title: "test puzzle"
            prompt: "predict"
            simulator: cache
            setup:
              policy: LRU
              size_lines: 2
              line_size_bytes: 64
              associativity: 1
              accesses: [0, 64]
            answer_kind: sequence
            answer_grammar: "two tokens of H or M"
            explanation: "both cold misses"
            hints:
              - "the cache starts cold"
        """

    def test_duplicate_ids_rejected(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "memory/a.yaml", self._minimal_puzzle("dup"))
            self._write(root, "memory/b.yaml", self._minimal_puzzle("dup"))
            with self.assertRaises(PuzzleDataError):
                PuzzleRegistry.from_directory(root)

    def test_unknown_simulator_rejected(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = self._minimal_puzzle("x").replace("simulator: cache", "simulator: quantum")
            self._write(root, "memory/x.yaml", body)
            with self.assertRaises(PuzzleDataError):
                PuzzleRegistry.from_directory(root)

    def test_broken_setup_rejected_at_load(self) -> None:
        """A setup the simulator cannot run must fail loading, not gameplay."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = self._minimal_puzzle("x").replace("policy: LRU", "policy: MRU")
            self._write(root, "memory/x.yaml", body)
            with self.assertRaises(PuzzleDataError):
                PuzzleRegistry.from_directory(root)

    def test_bad_difficulty_rejected(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = self._minimal_puzzle("x").replace("difficulty: 1", "difficulty: 9")
            self._write(root, "memory/x.yaml", body)
            with self.assertRaises(PuzzleDataError):
                PuzzleRegistry.from_directory(root)


if __name__ == "__main__":
    unittest.main()
