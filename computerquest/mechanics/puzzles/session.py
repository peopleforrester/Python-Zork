# ABOUTME: Owns the player's live micro-puzzle interaction (present, answer,
# ABOUTME: hint, skip) and the knowledge total derived from solved puzzles.

from __future__ import annotations

from enum import Enum
from typing import Any

from computerquest.config import KNOWLEDGE_AREAS
from computerquest.mechanics.puzzles.parsers import AnswerParseError
from computerquest.mechanics.puzzles.registry import PuzzleRegistry
from computerquest.mechanics.puzzles.types import MicroPuzzle

# Clean solves in one subject area before that area counts as 'strong'. Two is
# enough to be a signal without waiting until an area is nearly exhausted; the
# smallest area ships four puzzles.
_STRONG_SOLVES = 2


class HintMode(str, Enum):
    """What a hint costs the player.

    Decision 3 fixed one bargain for everyone: the first hint is free and the
    second marks the puzzle attempted, so a solve after it does not raise
    knowledge. That is the STANDARD mode and its behaviour is unchanged.

    The two additions change only the cost, never what a hint reveals, and
    none of them touches decision 5: knowledge stays a pure function of solved
    puzzles in every mode.
    """

    #: Hints are free and never mark a puzzle attempted. For a first playthrough,
    #: where quietly forfeiting knowledge for asking a question teaches nothing.
    LEARNING = "learning"
    #: Decision 3 as written. The default.
    STANDARD = "standard"
    #: Hints are withheld entirely, for a harder replay. The explanation shown
    #: after an answer is unaffected: strict means no help before committing,
    #: not learning nothing afterwards.
    STRICT = "strict"


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
        # What a hint costs (decision 9). Player-set, persisted with the save.
        self.hint_mode: HintMode = HintMode.STANDARD
        # Puzzles the player asked for help on or gave up on, in any mode.
        # Kept separate from attempted_puzzles, which is the *knowledge* cost
        # and is written only in STANDARD (decision 3). Standing has to read a
        # mode-independent signal, or the beginner mode reads as "strong" and
        # gets served the hardest puzzle first.
        self.struggled: set[str] = set()

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

    def area_standing(self, area: str) -> str:
        """How the player is faring in one subject area.

        Reads the two durable signals the session already keeps: puzzles solved,
        and puzzles attempted but still unsolved (a wrong answer or a costly
        hint records an attempt). Returns 'struggling', 'strong', or 'neutral'.

        Deliberately coarse. This orders what a room offers; it never unlocks
        anything, so a mistake here costs a player nothing but a reordering.
        """
        by_id = self.registry.by_id
        solved = sum(
            1 for p in self.player.solved_puzzles
            if p in by_id and by_id[p].subject_area == area
        )
        struggled_with = self.player.attempted_puzzles | self.struggled
        unresolved = sum(
            1 for p in struggled_with
            if p in by_id and by_id[p].subject_area == area
            and p not in self.player.solved_puzzles
        )

        if unresolved and unresolved >= solved:
            return "struggling"
        if solved >= _STRONG_SOLVES and not unresolved:
            return "strong"
        return "neutral"

    def _adaptive_order(self, puzzles: list[MicroPuzzle]) -> list[MicroPuzzle]:
        """Order a room's offer to match the player's standing.

        Struggling players meet the easiest available puzzle first, strong
        players the hardest; everyone else keeps the authored order. Sorting is
        stable, so equal-difficulty puzzles never move relative to each other.
        """
        if len(puzzles) < 2:
            return puzzles
        # A room's puzzles share a subject area in the shipped content, but
        # take the first as the reference rather than assuming it.
        standing = self.area_standing(puzzles[0].subject_area)
        if standing == "struggling":
            return sorted(puzzles, key=lambda p: p.difficulty)
        if standing == "strong":
            return sorted(puzzles, key=lambda p: -p.difficulty)
        return puzzles

    def gated_room_puzzles(self) -> list[MicroPuzzle]:
        """Unsolved puzzles in the current room that the soft difficulty
        gate shows (decision 2): difficulty 1 always; difficulty N needs a
        solved difficulty >= N-1 puzzle in the same subject area.

        The surviving puzzles are then ordered by the player's standing in the
        area (decision 7); the gate itself is unaffected.
        """
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
        return self._adaptive_order(shown)

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
        # Which puzzle leads is the player's standing to decide (decision 7).
        # Built from the gated list so this path cannot present a puzzle that
        # `solve` refuses to show: the two disagreed, and every single-puzzle
        # room made decision 2's gate decorative here.
        candidates = self.gated_room_puzzles()
        if not candidates:
            return ""
        primary = candidates[0].id
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

        if self.hint_mode is HintMode.STRICT:
            # Withheld before committing, but the post-answer explanation still
            # runs, so a strict player still learns from a wrong answer.
            return (
                "Hints are off in strict mode. Commit an answer with "
                "'answer <...>'; the explanation follows either way."
            )

        if self.hints_used >= len(puzzle.hints):
            return "No more hints for this puzzle."
        text = puzzle.hints[self.hints_used]
        self.hints_used += 1
        # Recorded in every mode, so standing does not depend on hint cost.
        self.struggled.add(puzzle.id)

        suffix = ""
        if self.hints_used >= 2 and self.hint_mode is HintMode.STANDARD:
            # Decision 3: the second and later hints give the answer's shape
            # away, so the puzzle counts as attempted from here on. Learning
            # mode deliberately waives this.
            self.player.attempted_puzzles.add(puzzle.id)
            suffix = "\n(That one cost you: this puzzle now counts as attempted.)"
        return f"Hint: {text}{suffix}"

    def skip(self) -> str:
        if self.current is None:
            return "No active puzzle to skip."
        # Setting a puzzle aside unsolved is a struggle signal too, and unlike
        # a hint it is available in strict mode. Without it, strict recorded
        # nothing and a stuck player still read as "strong".
        self.struggled.add(self.current.id)
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

        The tally is seeded from the canonical area list rather than from the
        dict being replaced. Seeding from the old dict made the result whatever
        that dict happened to hold: a save file with an extra area kept it, and
        one missing an area raised KeyError on the first puzzle scored into it.
        """
        totals: dict[str, float] = {area: 0.0 for area in KNOWLEDGE_AREAS}
        for puzzle_id in self.player.solved_puzzles:
            puzzle = self.registry.by_id.get(puzzle_id)
            if puzzle is not None:
                totals[puzzle.subject_area] += puzzle.knowledge_weight()
        self.player.knowledge = {
            area: (int(v) if float(v).is_integer() else v)
            for area, v in ((a, min(5.0, total)) for a, total in totals.items())
        }
