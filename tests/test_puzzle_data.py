#!/usr/bin/env python3
"""
ABOUTME: Data gate for the shipped puzzle tree — every YAML must be playable.
ABOUTME: New puzzle files cannot land without passing this (contract test layer 2).
"""

import unittest

from computerquest.mechanics.puzzles.registry import DATA_ROOT, load_registry
from computerquest.mechanics.simulators.base import AnswerKind

VALID_CATEGORIES = {"cpu", "memory", "storage", "networking", "security"}

_SHAPES: dict[AnswerKind, type | tuple[type, ...]] = {
    AnswerKind.SEQUENCE: list,
    AnswerKind.NUMBER: int,
    AnswerKind.BOOL: bool,
    AnswerKind.CHOICE: str,
    AnswerKind.MAPPING: dict,
}


class TestShippedPuzzleData(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_tree_is_not_empty(self) -> None:
        self.assertGreaterEqual(len(self.registry.by_id), 3)

    def test_every_puzzle_is_playable(self) -> None:
        """For each shipped puzzle: the simulator runs its setup and produces
        a canonical answer whose shape matches the declared answer_kind."""
        for puzzle in self.registry.by_id.values():
            with self.subTest(puzzle=puzzle.id):
                canonical = self.registry.canonical_answer(puzzle.id)
                self.assertIsInstance(canonical, _SHAPES[puzzle.answer_kind])

    def test_metadata_is_within_contract(self) -> None:
        for puzzle in self.registry.by_id.values():
            with self.subTest(puzzle=puzzle.id):
                self.assertIn(puzzle.component_category, VALID_CATEGORIES)
                self.assertIn(puzzle.subject_area, VALID_CATEGORIES)
                self.assertIn(puzzle.difficulty, (1, 2, 3))
                self.assertTrue(puzzle.prompt.strip())
                self.assertTrue(puzzle.explanation.strip())
                self.assertTrue(puzzle.answer_grammar.strip())

    def test_id_matches_filename_stem(self) -> None:
        """Convention from the contract: one file per puzzle, id == stem —
        keeps grep and review trivially navigable."""
        for path in DATA_ROOT.rglob("*.yaml"):
            with self.subTest(file=str(path)):
                self.assertIn(path.stem, self.registry.by_id)

    def test_file_category_dir_matches_component_category(self) -> None:
        for path in DATA_ROOT.rglob("*.yaml"):
            puzzle = self.registry.by_id[path.stem]
            self.assertEqual(
                puzzle.component_category,
                path.parent.name,
                f"{path} lives in {path.parent.name}/ but declares "
                f"component_category={puzzle.component_category}",
            )


if __name__ == "__main__":
    unittest.main()
