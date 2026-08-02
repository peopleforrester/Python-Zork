#!/usr/bin/env python3
# ABOUTME: Authoring tool: validates the puzzle tree and prints canonical answers.
# ABOUTME: The loader already validates; this reports legibly instead of crashing.

"""Validate puzzle YAML and show what each puzzle's answer actually is.

`PuzzleRegistry.from_directory` is the validator: it runs every setup through
its named simulator at load time, so a broken puzzle cannot ship. What it does
not do is report nicely, and it stops at the first bad file. This walks the tree,
reports every problem at once, and prints the canonical answer for each puzzle.

Printing the answer is the point. It is computed from simulator code at runtime
and stored nowhere, so an author writing a new puzzle has no way to check that
their prompt matches their setup without running Python by hand. Every shipped
file records the answer in a header comment for exactly this reason, and this
tool checks that record is still true.

Usage:
    uv run python scripts/validate_puzzles.py            # whole tree
    uv run python scripts/validate_puzzles.py <path>     # one file or directory
    uv run python scripts/validate_puzzles.py --quiet    # problems only
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from computerquest.mechanics.puzzles.registry import (  # noqa: E402
    DATA_ROOT,
    SIMULATORS,
    PuzzleDataError,
    _parse_file,
    _validate_playable,
)
from computerquest.world.architecture import ComputerArchitecture  # noqa: E402


def answer_forms(answer: Any) -> set[str]:
    """Every spelling of one answer token an author might reasonably write.

    Numbers get their hex forms too: the two translate puzzles state their
    canonical answer as `0x1ABC` rather than 6844, which is the clearer way to
    write an address and must not be reported as a missing answer.
    """
    text = str(answer).lower()
    # bool is an int subclass, so this order matters: hex(True) is '0x1'.
    if isinstance(answer, bool) or not isinstance(answer, int):
        return {text}
    return {text, hex(answer), f"0x{answer:x}"}


def check_header(source: str, answer: Any) -> list[str]:
    """Report if the file's header comments do not state the canonical answer.

    Only `#` lines count. Searching the whole file would match the prompt body,
    where the numbers of the setup naturally appear, and pass for free.
    """
    comments = "\n".join(
        line for line in source.splitlines() if line.lstrip().startswith("#")
    ).lower()
    if not comments.strip():
        return ["no header comment recording the canonical answer"]

    tokens = answer if isinstance(answer, list) else [answer]
    missing = [
        str(token) for token in tokens
        if not any(form in comments for form in answer_forms(token))
    ]
    if missing:
        return [f"header comment does not state {missing} (answer is {answer!r})"]
    return []


@dataclass
class Report:
    answers: dict[str, Any] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)
    unbound: list[str] = field(default_factory=list)


def _bound_puzzle_ids() -> set[str]:
    """Puzzle ids some room actually offers.

    Binding is a literal list in architecture.py; the YAML's component_category
    is descriptive and places nothing. A puzzle absent from that list loads,
    validates, and is unreachable, so it is worth naming.
    """
    architecture = ComputerArchitecture()
    # bind_puzzles runs inside setup(), not the constructor. Without this the
    # room map is empty, every puzzle reads as unbound, and the check inverts
    # from "nothing is unreachable" to "everything is".
    architecture.setup()
    return {
        puzzle_id
        for room in architecture.rooms.values()
        for puzzle_id in (getattr(room, "puzzles", None) or [])
    }


def check_tree(root: Path, check_binding: bool = False) -> Report:
    """Validate every YAML under `root`, collecting problems rather than raising."""
    report = Report()
    paths = [root] if root.is_file() else sorted(root.rglob("*.yaml"))

    for path in paths:
        try:
            puzzle = _parse_file(path)
            _validate_playable(puzzle, path)
        except PuzzleDataError as exc:
            report.problems.append(str(exc))
            continue

        if puzzle.id != path.stem:
            report.problems.append(f"{path}: id {puzzle.id!r} does not match the filename")

        answer = SIMULATORS[puzzle.simulator].run(puzzle.setup)
        report.answers[puzzle.id] = answer
        report.problems.extend(f"{path}: {p}" for p in check_header(path.read_text(), answer))

    if check_binding:
        bound = _bound_puzzle_ids()
        report.unbound = sorted(set(report.answers) - bound)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=str(DATA_ROOT),
                        help="a puzzle file or a directory of them")
    parser.add_argument("--quiet", action="store_true", help="print problems only")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"no such path: {root}")
        return 2

    # Binding is only meaningful for the shipped tree; a one-file check would
    # otherwise report that file as unreachable whenever it is bound elsewhere.
    report = check_tree(root, check_binding=root.resolve() == DATA_ROOT.resolve())

    if not args.quiet:
        for puzzle_id, answer in sorted(report.answers.items()):
            print(f"  {puzzle_id:32} {answer!r}")
        print(f"\n{len(report.answers)} puzzles validated")

    for problem in report.problems:
        print(f"PROBLEM: {problem}")
    for puzzle_id in report.unbound:
        print(f"UNREACHABLE: {puzzle_id} is bound to no room "
              f"(add it to architecture.py::bind_puzzles)")

    if report.problems or report.unbound:
        print(f"\n{len(report.problems) + len(report.unbound)} problem(s) found.")
        return 1
    if not args.quiet:
        print("All puzzles valid, reachable, and documented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
