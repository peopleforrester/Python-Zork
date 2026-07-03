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
