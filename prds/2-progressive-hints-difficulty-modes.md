# PRD 2: Progressive hints + difficulty/tutorial modes

Status: **backlog** (not started, not approved)
Adapted from KubeQuest PRD #50.
Contract affected: `docs/architecture-microquiz.md` decision 3 (tiered hints).

## Why

The bones already exist and are half-used. Decision 3 gives every puzzle an
ordered hint list where the first is free and the second onward marks the puzzle
attempted, so a first-time-correct after a costly hint does not raise knowledge.
What is missing is any way to change that bargain.

There is no learning mode for a new player who wants help freely, and no way to
switch help off for a harder replay. The hint cost is a single fixed rule applied
to everyone.

Separately, decision 7 (adaptive difficulty) already computes a per-subject-area
standing of `struggling`, `strong`, or `neutral` from solved and
attempted-but-unsolved puzzles. Today that signal drives exactly one thing: the
order a room offers its puzzles. It is the natural input to hint generosity and
is currently going to waste.

## Requirements

- **Difficulty tiers** selectable by the player, at minimum: a learning mode
  where hints are free and never mark a puzzle attempted, the current default,
  and a strict mode where hints are unavailable.
- **Hints escalate per puzzle and remember they were asked.** Today
  `hints_used` is a counter into a static list; a second request for the same
  hint tier should acknowledge it has been asked rather than repeat verbatim.
- **The solution stays reachable** in every mode. Strict mode removes hints, not
  the explanation shown after an answer.
- **Reuse the adaptive-difficulty standing.** A `struggling` area is the
  strongest existing signal for offering more help; a `strong` one for offering
  less.
- Mode is player state, so it must survive save/load. Coordinate with PRD 1
  Feature A so there is one schema bump, not two.

## Contract impact

Decision 3 fixes the hint bargain as a global rule. Making it mode-dependent is
an amendment, following the decision 7 precedent: strike or qualify the rule,
add a numbered decision, record the new sha, update the ABOUTME headers in
`puzzles/types.py` and `puzzles/__init__.py`.

The knowledge model must not move. Knowledge stays a pure function of solved
puzzles, and `PuzzleSession` stays its single writer. A learning mode that
granted knowledge for hinted solves would break decision 5 and reintroduce
exactly the tourism the redesign removed.

## Deliverable

Mode selection surfaced in-game, hint behaviour varying by mode, mode persisted,
and tests covering each mode's effect on `attempted_puzzles` and on the
knowledge meter.
