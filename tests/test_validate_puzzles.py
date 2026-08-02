#!/usr/bin/env python3
"""
ABOUTME: Tests the puzzle-authoring validator and the invariants it enforces.
ABOUTME: The header-comment check pins a claim nothing else verified.
"""

import importlib.util
import pathlib
import sys
import tempfile
import unittest

from computerquest.mechanics.puzzles import load_registry

_SPEC = importlib.util.spec_from_file_location(
    "validate_puzzles", pathlib.Path(__file__).parent.parent / "scripts" / "validate_puzzles.py"
)
validate = importlib.util.module_from_spec(_SPEC)
# @dataclass resolves annotations through sys.modules[cls.__module__], so the
# module has to be registered before exec, not after.
sys.modules[_SPEC.name] = validate
_SPEC.loader.exec_module(validate)

DATA_ROOT = pathlib.Path(__file__).parent.parent / "computerquest" / "mechanics" / "puzzles" / "data"


class TestAnswerFormatting(unittest.TestCase):
    """A number answer may legitimately be written in hex in the header
    comment, which is how the two translate puzzles state theirs."""

    def test_a_decimal_is_recognised(self):
        self.assertIn("36", validate.answer_forms(36))

    def test_hex_forms_are_recognised(self):
        forms = validate.answer_forms(6844)
        self.assertTrue({"0x1abc"} <= forms, forms)

    def test_a_string_answer_is_itself(self):
        self.assertEqual(validate.answer_forms("boot_sector_virus"), {"boot_sector_virus"})

    def test_a_bool_is_not_treated_as_a_number(self):
        """bool is an int subclass, so hex(True) would offer '0x1'."""
        self.assertEqual(validate.answer_forms(True), {"true"})


class TestShippedTreeIsClean(unittest.TestCase):
    """The validator must pass on the tree it ships beside."""

    @classmethod
    def setUpClass(cls):
        # check_binding must be on, or `unbound` is always empty and the
        # reachability assertion below passes without testing anything.
        cls.report = validate.check_tree(DATA_ROOT, check_binding=True)

    def test_no_problems_are_reported(self):
        self.assertEqual(self.report.problems, [], "\n".join(self.report.problems))

    def test_every_puzzle_is_covered(self):
        self.assertEqual(len(self.report.answers), len(load_registry().by_id))

    def test_every_puzzle_is_bound_to_a_room(self):
        """A puzzle bound nowhere loads, validates, and is unreachable, since
        binding is a literal list in architecture.py rather than anything the
        YAML declares."""
        self.assertEqual(self.report.unbound, [])


class TestHeaderCommentCheck(unittest.TestCase):
    """Every shipped file states its canonical answer in a header comment. That
    was the author's claim and nothing verified it, so a simulator change could
    leave the comment contradicting the code it documents."""

    def test_a_comment_stating_the_answer_passes(self):
        self.assertEqual(
            validate.check_header("# answer: 36 ticks\nid: x\n", 36), []
        )

    def test_a_comment_missing_the_answer_is_reported(self):
        self.assertTrue(validate.check_header("# answer: 12 ticks\nid: x\n", 36))

    def test_a_file_with_no_header_comment_is_reported(self):
        self.assertTrue(validate.check_header("id: x\n", 36))

    def test_a_sequence_needs_every_element(self):
        header = "# answer: boot_sector_virus\nid: x\n"
        self.assertTrue(validate.check_header(header, ["boot_sector_virus", "rootkit_virus"]))

    def test_a_sequence_with_every_element_passes(self):
        header = "# answer: boot_sector_virus then rootkit_virus\nid: x\n"
        self.assertEqual(
            validate.check_header(header, ["boot_sector_virus", "rootkit_virus"]), []
        )

    def test_only_comment_lines_are_searched(self):
        """The answer appearing in the prompt body is not the author stating
        it; the check would otherwise pass on almost every file for free."""
        self.assertTrue(validate.check_header("id: x\nprompt: the answer is 36\n", 36))


class TestBadTreeIsRejected(unittest.TestCase):
    """The validator's job is to report author errors legibly rather than
    crash the game at startup."""

    def _tree(self, name, body):
        # dir="." keeps the scratch tree inside the repo rather than /tmp, and
        # the context manager removes it however the test exits.
        holder = tempfile.TemporaryDirectory(dir=".")
        self.addCleanup(holder.cleanup)
        root = pathlib.Path(holder.name)
        (root / "cpu").mkdir()
        (root / "cpu" / name).write_text(body)
        return root

    def test_an_answer_kind_mismatch_is_reported(self):
        body = (
            '# answer: 7\nid: bad_kind\ncomponent_category: cpu\nsubject_area: cpu\n'
            'difficulty: 1\ntitle: "t"\nsimulator: pipeline\nprompt: "p"\n'
            'setup:\n  stages: 5\n  forwarding: true\n  instructions:\n'
            '    - ["ADD", ["R1", "R2"], "R3"]\n'
            'answer_kind: sequence\nanswer_grammar: "g"\nexplanation: "e"\n'
        )
        report = validate.check_tree(self._tree("bad_kind.yaml", body))
        self.assertTrue(any("answer_kind" in p for p in report.problems), report.problems)

    def test_invalid_yaml_is_reported_not_raised(self):
        report = validate.check_tree(self._tree("broken.yaml", "{not: valid: yaml:\n"))
        self.assertTrue(report.problems)


if __name__ == "__main__":
    unittest.main()
