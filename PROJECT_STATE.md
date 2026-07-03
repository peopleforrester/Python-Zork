# Project State: Python-Zork

Phase: 1.3 Approve
Approved: pending

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Lifecycle header per state-persistence schema; narrative body below.

## Lifecycle

Current unit of work: **micro-puzzle implementation (tk-a7098e)** per `docs/architecture-microquiz.md`.

- [x] 1.1 Research (teaching-games spike in mrf-knowledge, 2026-06-22)
- [x] 1.2 Plan (architecture-microquiz.md drafted b8a7a9b; six decisions resolved 4279a5a)
- [ ] 1.3 Approve  ← you are here (Michael directed Direction C and the decision calls; formal contract seal pending)
- [ ] 2.1 Test
- [ ] 2.2 Implement
- [ ] 2.3 Verify
- [ ] 3.1 Stage
- [ ] 3.2 Confirm CI
- [ ] 3.3 Promote

Prior unit (senior-review remediation + Step 4.2/4.3 + save/load) completed through 3.3 — promoted to `main` at 8ec133c on 2026-06-22.

## Contracts

_(none sealed yet under the lifecycle schema. Decision history predating the schema lives in `decisions.md` and project memory: Step 1.2 REMOVE save/load [later restored by tk-24fa9f], Step 1.3 GATE minigames, Step 3.2 DELETE data/*.json, Step 3.6 WIRE health bar, plus the six micro-puzzle architecture calls in docs/architecture-microquiz.md.)_

## Current Plan

**Micro-puzzle system (Direction C, predict-and-verify).** Full blueprint in `docs/architecture-microquiz.md` (decisions resolved 2026-06-26); deep-end minigame design in `docs/design-minigames.md`; research grounding in `mrf-knowledge/game-design/2026-06-22_teaching-games-text-adventure-pivot.md`.

Migration order (each step lands green): 1 simulators → 2 puzzle infra → 3 player/architecture wiring → 4 command surface (`solve`/`answer`/`hint`/`skip`) → 5 content fill (28 puzzles) → 6 knowledge-meter cutover → 7 minigames consume simulators, flip `ENABLE_MINIGAMES` → 8 frontend per-room puzzle state.

Remaining tracked task: `tk-a7098e` (4.1 minigames) — now unblocked; it is steps 1–7 above. Step 4.2's browser verification is DONE (2026-07-03, headless Chromium walkthrough): welcome renders in xterm, typed command flows through the keystroke buffer into Game.feed, terminal prints the move, map re-renders live (Turn 1, current node CPU Package → Core 1). Three defects found and fixed during the walkthrough (d1b51e1).

## Branch & Tests

- Branch: `staging`
- Working tree: clean
- Last CI: green on staging @ d1b51e1 (run 28671675746)
- `staging` and `main` are in sync at d1b51e1 (promoted 2026-07-03 after the browser walkthrough cleared the verification gate).
- Tests: 150/150 via `uv run pytest`; ruff clean; mypy clean (required in CI, Python 3.11+3.12 matrix)
- Canonical test fixture: `tests/_helpers.py::build_real_game`

## Phase History

_(append-only. Each phase transition adds one line, oldest first.)_
- 2026-04-28T00:00:00Z pre-lifecycle · remediation plan persisted (plan.md, tasks.yaml)
- 2026-05-04T00:00:00Z pre-lifecycle · Weeks 1–3 remediation complete on staging
- 2026-06-22T00:00:00Z pre-lifecycle · master renamed to main; staging promoted (8ec133c)
- 2026-06-22T00:00:00Z 1.1 research spike saved (teaching-games canon)
- 2026-06-26T00:00:00Z 1.1 → 1.2 architecture-microquiz.md decisions resolved (4279a5a)
- 2026-07-01T00:00:00Z init-state migration → lifecycle schema adopted at Phase 1.3
- 2026-07-03T00:00:00Z Step 4.2 browser-verified via headless walkthrough; 3 defects fixed (d1b51e1); staging promoted to main

## Narrative history (pre-migration body, condensed)

The senior-developer review (2026-04-19) produced a 26-step remediation plan. All of it shipped: Week 1 critical bugs (hotkey collision, save/load stub removal, minigame gating, server hardening, real-Game test fixtures), Week 2 tooling (pyproject consolidation, version single-sourcing, CI, repo hygiene), Week 3 refactor (game.py split, dead JSON removal, difflib matcher, type annotations, motherboard de-dup, health-bar wiring, constants), Week 4 features (virus-name predicate, NPC pop bug), LP cleanup tail, save/load reimplementation (tk-24fa9f), and Step 4.2 (Game in-process in server.py + GameMap live-state wiring; browser verification pending).

Strategy pivot 2026-06-22: research spike found the game's "knowledge rises with visits" loop sits in the instructionist failed canon. Direction C adopted — keep the exploration shell, make knowledge rise on solved predict-and-verify micro-puzzles checked by real simulators.
