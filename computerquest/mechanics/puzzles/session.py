# ABOUTME: Owns the player's live micro-puzzle interaction (present, answer,
# ABOUTME: hint, skip) and the knowledge total derived from solved puzzles.

from __future__ import annotations

from typing import Any

from computerquest.mechanics.puzzles.parsers import AnswerParseError
from computerquest.mechanics.puzzles.registry import PuzzleRegistry
from computerquest.mechanics.puzzles.types import MicroPuzzle


class PuzzleSession:
    """The puzzle half of a play session.

    Holds the transient state a puzzle interaction needs (which puzzle is
    active, how many hints it has cost, which rooms have already auto-prompted)
    and reads durable progress from the player. Contract:
    docs/architecture-microquiz.md.
    """

    def __init__(self, registry: PuzzleRegistry, player: Any, rooms: dict[str, Any]) -> None:
        self.registry = registry
        self.player = player
        self.rooms = rooms

        # current persists across rooms; it ends on answer or skip.
        self.current: MicroPuzzle | None = None
        self.hints_used = 0
        # Session-only: each room auto-presents its primary puzzle once
        # per session (decision 4).
        self.prompted_rooms: set[str] = set()

    # --- room helpers -------------------------------------------------------

    def current_room_id(self) -> str | None:
        """The rooms-dict key for the player's location.

        Components carry their key (assign_room_keys), so this is an attribute
        read. Falls back to a scan for components built outside a world, which
        tests do.
        """
        location = self.player.location
        key: str | None = getattr(location, "key", None)
        if key is not None and self.rooms.get(key) is location:
            return key
        for room_id, room in self.rooms.items():
            if room is location:
                return room_id
        return None

    def gated_room_puzzles(self) -> list[MicroPuzzle]:
        """Unsolved puzzles in the current room that the soft difficulty
        gate shows (decision 2): difficulty 1 always; difficulty N needs a
        solved difficulty >= N-1 puzzle in the same subject area."""
        by_id = self.registry.by_id
        shown: list[MicroPuzzle] = []
        for puzzle_id in self.player.location.puzzles:
            puzzle = by_id.get(puzzle_id)
            if puzzle is None:
                continue
            if puzzle.id in self.player.solved_puzzles:
                continue
            if puzzle.difficulty > 1:
                unlocked = any(
                    by_id[s].subject_area == puzzle.subject_area
                    and by_id[s].difficulty >= puzzle.difficulty - 1
                    for s in self.player.solved_puzzles
                    if s in by_id
                )
                if not unlocked:
                    continue
            shown.append(puzzle)
        return shown

    # --- presentation -------------------------------------------------------

    def present(self, puzzle: MicroPuzzle, auto: bool = False) -> str:
        self.current = puzzle
        self.hints_used = 0
        lines = [
            f"┏━━━ PUZZLE: {puzzle.title} ━━━┓",
            "",
            puzzle.prompt.rstrip(),
            "",
            f"Answer with 'answer <...>' ({puzzle.answer_grammar}).",
            "A 'hint' is available; 'skip' puts the puzzle aside.",
        ]
        if auto:
            lines.append("(Type 'skip' to put this aside and keep exploring.)")
        return "\n".join(lines)

    def maybe_auto_prompt(self) -> str:
        room = self.player.location
        room_id = self.current_room_id()
        if not room.puzzles or room_id is None:
            return ""
        if self.current is not None:
            return ""
        if room_id in self.prompted_rooms:
            return ""
        primary = room.puzzles[0]
        if primary in self.player.solved_puzzles or primary in self.player.attempted_puzzles:
            return ""
        self.prompted_rooms.add(room_id)
        return self.present(self.registry.by_id[primary], auto=True)

    def list_room_puzzles(self) -> str:
        shown = self.gated_room_puzzles()
        if not shown:
            return "There is no puzzle available here."
        lines = ["Puzzles in this room:"]
        for puzzle in shown:
            lines.append(f"  - {puzzle.id} (difficulty {puzzle.difficulty}): {puzzle.title}")
        lines.append("Enter 'solve <id>' to begin one, or 'solve' for the first.")
        return "\n".join(lines)

    # --- interaction --------------------------------------------------------

    def start(self, puzzle_id: str | None = None) -> str:
        room = self.player.location
        if puzzle_id:
            # Explicit id bypasses the soft gate but must live in this room.
            if puzzle_id not in room.puzzles or puzzle_id not in self.registry.by_id:
                return f"There is no puzzle named {puzzle_id!r} in this room."
            return self.present(self.registry.by_id[puzzle_id])

        shown = self.gated_room_puzzles()
        if not shown:
            return "There is no puzzle here. Explore other components and try 'solve' there."
        if len(shown) > 1:
            return self.list_room_puzzles()
        return self.present(shown[0])

    def answer(self, raw: str) -> str:
        if self.current is None:
            return "No active puzzle. Enter 'solve' in a room that has one."
        puzzle = self.current
        try:
            verdict = self.registry.evaluate(puzzle.id, raw)
        except AnswerParseError as exc:
            # Wrong shape is never graded; the puzzle stays active.
            return str(exc)

        if not verdict.correct and not verdict.positions and verdict.summary.startswith("answer has"):
            # Token-count mismatch is a shape problem, not a wrong answer:
            # do not grade, do not record an attempt.
            return f"I need an answer like: {puzzle.answer_grammar}"

        self.player.attempted_puzzles.add(puzzle.id)
        self.current = None
        self.hints_used = 0

        lines = []
        if verdict.correct:
            self.player.solved_puzzles.add(puzzle.id)
            before = self.player.knowledge.get(puzzle.subject_area, 0)
            self.recompute_knowledge()
            after = self.player.knowledge[puzzle.subject_area]
            lines.append(f"Correct! {puzzle.title} solved.")
            if after > before:
                lines.append(f"[ {puzzle.subject_area} knowledge: {before} -> {after} ]")
        else:
            lines.append(f"Not quite: {verdict.summary}.")
        for pos in verdict.positions:
            mark = "ok" if pos.matched else f"expected {pos.expected}"
            lines.append(f"  {pos.index + 1}. {pos.given} ({mark})")
        lines.append("")
        lines.append(puzzle.explanation.rstrip())
        if not verdict.correct:
            lines.append("")
            lines.append("Run 'solve' to try again whenever you like.")
        return "\n".join(lines)

    def hint(self) -> str:
        if self.current is None:
            return "No active puzzle. Enter 'solve' in a room that has one."
        puzzle = self.current
        if self.hints_used >= len(puzzle.hints):
            return "No more hints for this puzzle."
        text = puzzle.hints[self.hints_used]
        self.hints_used += 1
        suffix = ""
        if self.hints_used >= 2:
            # Decision 3: the second and later hints give the answer's shape
            # away, so the puzzle counts as attempted from here on.
            self.player.attempted_puzzles.add(puzzle.id)
            suffix = "\n(That one cost you: this puzzle now counts as attempted.)"
        return f"Hint: {text}{suffix}"

    def skip(self) -> str:
        if self.current is None:
            return "No active puzzle to skip."
        title = self.current.title
        self.current = None
        self.hints_used = 0
        return f"Putting '{title}' aside. Enter 'solve' any time to pick it back up."

    # --- derived knowledge --------------------------------------------------

    def recompute_knowledge(self) -> None:
        """Knowledge is a pure function of solved puzzles (decision 5):
        min(5, sum of difficulty * 0.5 + 0.5 per solved puzzle in the
        area). Visits, scans, and quarantines no longer contribute.

        This is the single writer of player.knowledge; see the knowledge
        note in docs/architecture-microquiz.md.
        """
        totals: dict[str, float] = {area: 0.0 for area in self.player.knowledge}
        for puzzle_id in self.player.solved_puzzles:
            puzzle = self.registry.by_id.get(puzzle_id)
            if puzzle is not None:
                totals[puzzle.subject_area] += puzzle.knowledge_weight()
        self.player.knowledge = {
            area: (int(v) if float(v).is_integer() else v)
            for area, v in ((a, min(5.0, total)) for a, total in totals.items())
        }
