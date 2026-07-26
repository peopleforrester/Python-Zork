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
