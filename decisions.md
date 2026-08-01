# Decisions Log

Append-only audit trail of approvals, amendments, backward steps, and conditional-skip rationales. See the state-persistence rule for schema.

## 2026-07-01T00:00:00Z · init · state persistence migrated to lifecycle schema

init-state ran in this repo. PROJECT_STATE.md predated the lifecycle
schema; header prepended, body refreshed to current facts (the old body
had gone stale: it still listed Step 4.2 as blocked and the four
remediation decisions as open). Pre-migration copy preserved at
/tmp/PROJECT_STATE.md.bak.20260627-164249 and in git history.

Decisions made before this log existed, imported for the record (full
rationale lives in project memory and the referenced docs):

- 2026-05-02 · Step 1.2 · save/load REMOVED (placeholder silently lost
  data). Later reimplemented properly as tk-24fa9f on 2026-06-03.
- 2026-05-02 · Step 1.3 · minigames GATED behind ENABLE_MINIGAMES=False
  pending real implementations.
- 2026-06-04 · Step 3.2 · dead data/*.json DELETED (zero consumers;
  architecture.py::make_components() is the single source).
- 2026-06-04 · Step 3.6 · health bar WIRED to real player (dead hasattr
  branch removed).
- 2026-06-22 · strategy · Direction C adopted: predict-and-verify
  micro-puzzles replace visit-based knowledge accrual. Grounded in the
  teaching-games research spike (mrf-knowledge/game-design).
- 2026-06-26 · architecture · six micro-puzzle design calls resolved in
  docs/architecture-microquiz.md (multi-puzzle rooms capped at 3, soft
  difficulty gating, tiered hints, first-visit auto-prompt, cap-5
  difficulty-weighted knowledge, per-simulator fidelity statements).

## 2026-07-04T00:00:00Z · 1.3 · microquiz architecture approved

Michael approved docs/architecture-microquiz.md as the contract for
the predict-and-verify micro-puzzle unit (tk-a7098e).
sha256:cde83dbaa90b18bdec1c05ffadb18f1d603f70ee0dc8e9b536820610c6bc8555.
Alternatives (stay-the-course portfolio piece; full Zachtronics-style
pivot) were rejected in the 2026-06-22 research spike. Implementation
follows the doc's eight-step migration plan, TDD-first per step.

## 2026-07-06T00:00:00Z · amendment · prose-style pass over the contract doc

Michael directed an AI-isms sweep over all repo prose. The sealed
contract (docs/architecture-microquiz.md) had 38 em-dashes plus a few
splices; all replaced per the prose-style rule. No decision, schema,
verb, or plan-step content changed. New sha256:8abdc57a3d45. Same pass
cleaned README (also fixing stale PTY-era architecture and security
text), PROJECT_STATE, plan.md, design-minigames.md, and the three
puzzle YAML files.

## 2026-07-25T00:00:00Z · reconciliation · state files corrected to actual shipped state

PROJECT_STATE.md and tasks.yaml had drifted: they still declared Phase 2.1
Test, 150 tests, and CI at d1b51e1, while the repo had shipped the full
eight-step microquiz unit plus a frontend test-suite unit and an npm-audit
cleanup, all promoted to main (all refs at 6349499, 277 pytest + 14 vitest +
3 Playwright e2e green). Marked tk-a7098e done, advanced the lifecycle
checklist to 3.3 complete, updated Branch & Tests, and appended phase-history
lines. No code changed. Recorded the open save/load contradiction (code keeps
save/load; an earlier decision said remove it) as still needing a call from
Michael.

## 2026-07-25T00:00:00Z · correction · save/load is not an open contradiction

Corrects the prior entry, which called the wired save/load an "open
contradiction." It is not. The Step 1.2 decision (2026-05-02) removed only the
placeholder save/load that silently lost data (99be8ed) and filed a follow-up
to port a real one from archive/saveload.py. That follow-up (tk-24fa9f) shipped
the real implementation (510ae26). The current SaveLoadSystem plus
save/load/deletesave commands are the intended end state. No decision from
Michael is pending on this.

## 2026-07-26T00:00:00Z · review · code-review remediation scope approved and shipped

A five-lens review (architecture, Python correctness, mechanics, frontend/server,
refactor) surfaced eight bugs plus cleanup and hardening opportunities. Michael
chose scope "Bugs + cleanup" (Phases 1-3) plus deploy/security hardening (Phase
4), and explicitly DEFERRED the larger structural work (game.py god-object split,
knowledge single-writer, visited/id-space dedup) as not-a-live-bug. Shipped in
four commits a43897d..efede42, staging CI green, ff-merged to main. Test count
277 to 297. The deferred structural items are recorded in PROJECT_STATE for a
future decision.

## 2026-07-27T00:00:00Z · refactor · deferred structural work completed

Michael asked for the structural items the earlier review had deferred. All
four shipped: static-content extraction out of game.py (guarded by a
byte-exact golden fixture), PuzzleSession extraction, knowledge reduced to a
single writer, and the visited/id-space duplication removed.

The visited work turned out to fix a live defect rather than a latent one: at
turn 0 the starting room was recorded visited in map_grid but not on the
Component, so the ASCII map and the React map disagreed, and the web map
reported 0/35 visited while the player stood in a room. map_grid is now
derived from Component.visited.

Knowledge rewards were removed rather than made durable, because the approved
contract (architecture-microquiz.md, Knowledge meter) defines knowledge as a
function of demonstrated solves; granting it from an achievement would be a
contract deviation requiring re-approval, not a bug fix.

game.py 1114 -> 772 lines, tests 297 -> 318. CI green, promoted to main,
redeployed to Railway and verified live in a browser.

## 2026-07-31T00:00:00Z · 1.3 · amendment · decision 7, adaptive difficulty

Michael asked for the adaptive-difficulty feature, which the sealed contract
listed under "Out of scope" ("the puzzle order is room-determined, not
player-skill-determined; a future pass could re-order based on solve history").
Implementing it therefore required amending the contract, not just coding.

Two design forks were put to Michael before any source was touched. He chose
(a) reorder within a room in both directions, leaving the gate and the
knowledge formula alone, over the wider options of relaxing the unlock gate for
strong players or adding scaffolding for strugglers; and (b) silent adaptation
over announcing it, so a struggling player is not told the game thinks they are
struggling.

The narrow scope is the point: because the feature only reorders, it cannot
open a gate or grant knowledge, so a wrong standing costs a player nothing but
which puzzle appears first. Standing reuses signals already tracked, so no new
save state and no schema bump.

Contract body updated (decision 7 added, the out-of-scope bullet struck);
new sha256:2949c0833fdf.

## 2026-08-01T00:00:00Z · 2.2 · Phase 0 hardening (PRD 1)

Michael approved PRD 1 with Feature C parked, Feature A scoped to puzzle state
only, Feature B scoped to the one zero-code puzzle, and Phase 0 first.

Phase 0 closed two defects found during research and one documentation drift.

Shipped puzzle answers were unguarded: the canonical answer is recomputed from
simulator code on every call and stored nowhere, so a simulator edit rewrote
shipped content silently. Demonstrated by mutating the signature scanner to take
the last match instead of the first, which flipped signature_first_match's answer
to contradict its own printed explanation while all 404 tests passed. All 28
answers are now pinned to literals.

Author-supplied setup values were unbounded, and the registry validates a puzzle
by running it. A single integer made the cache simulator allocate to OOM in
about five seconds, and SSTF is quadratic so a long request list hung with no
memory signature. Both now raise immediately with a naming message. The bounds
sit three to four orders of magnitude above anything shipped content uses.

The validator also relabelled MemoryError as an empty "setup is not runnable: "
and swallowed watchdog signals; those now propagate. A missing answer_kind
cross-check was added at the same seam, since a mismatch previously loaded
cleanly and then made every answer wrong forever with no error.

The contract's per-simulator fidelity statements were drafted before the
simulators existed and had drifted: they promised ARP and link-layer framing
never implemented, structural hazards not modelled, and an SSD remap counter
that does not exist, while omitting the first-match rule signature_first_match
depends on. Reconciled to the module docstrings verbatim. No simulator behaviour
changed; new sha256:65767d1a411e.

## 2026-08-01T00:00:00Z · 1.3 · amendment · decision 8, in-flight puzzle persistence

Approved as part of PRD 1, scoped by Michael to puzzle state only. Minigame
state stays out of scope, so `design-minigames.md` is untouched and its
"do not re-litigate" note stands.

A save now records the active puzzle's id, hints spent, and the rooms that have
already auto-prompted. The body is never serialized; only the id, so a stale
save cannot resurrect deleted or rewritten content. Restore tolerates drift the
way the loader already tolerates unknown component ids: an unresolvable id
clears the puzzle and zeroes the hint count, a shortened hint list clamps the
counter, unknown prompted rooms are inert.

The original exclusion justified itself only by mirroring the minigame decision,
whose rationale was that active sessions are not long-running state worth
persisting. That reasoning survives for minigames and does not for puzzles:
`prompted_rooms` is what stops a room re-offering a puzzle the player set aside,
and losing the hint counter while keeping its durable consequence meant a
reloaded game handed out two more free hints on an already-attempted puzzle.

Schema 1.1 to 1.2; 1.0 and 1.1 saves still load with an empty session. Knowledge
untouched. New contract sha256:73cd234c9b75.

Prose note: the antithesis count in the contract rose by one during Phase 0's
fidelity reconciliation, from quoting tlb.py's docstring verbatim ("an unmapped
VPN is an authoring error, not a simulated fault"). Rewording it would restore
the doc/code drift that reconciliation removed, so it stays.

## 2026-08-01T00:00:00Z · 1.3 · amendment · decision 9, difficulty modes

PRD 2. Decision 3 fixed one hint bargain for every player: first free, second
marks the puzzle attempted. That is now `standard` and is unchanged.

`learning` waives the attempt mark so a new player can lean on hints without
quietly forfeiting the knowledge they are about to earn. `strict` withholds
hints for a harder replay but deliberately leaves the post-answer explanation
running, since the explanation is where the teaching lives and removing it would
make strict mode punitive rather than harder.

Knowledge was the thing to protect. Decision 5 makes it a pure function of
solved puzzles with PuzzleSession as the single writer, so the modes were built
to touch only whether a hint records an attempt. A test asserts the meter does
not move for any of the three modes.

Schema 1.2 to 1.3 for the preference. PRD 2 had asked to share a bump with
Feature A, which was no longer possible because A shipped first; both bumps are
additive and older saves restore `standard`. New sha256:3a650b2e76b6.
