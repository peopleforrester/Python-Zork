# Project State: Python-Zork

Phase: 3.3 Promote (complete) — no unit in flight
Approved: 2026-07-04T00:00:00Z by Michael (sha256:cde83dbaa90b; prose-style amendment 2026-07-06 sha256:8abdc57a3d45)

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Lifecycle header per state-persistence schema; narrative body below.

## Lifecycle

No unit of work in flight. Last unit: **micro-puzzle implementation (tk-a7098e)** per `docs/architecture-microquiz.md`, complete and promoted; followed by a frontend test-suite unit and an npm-audit cleanup unit, both promoted.

- [x] 1.1 Research (teaching-games spike in mrf-knowledge, 2026-06-22)
- [x] 1.2 Plan (architecture-microquiz.md drafted b8a7a9b; six decisions resolved 4279a5a)
- [x] 1.3 Approve (Michael, 2026-07-04; sha256:cde83dbaa90b)
- [x] 2.1 Test (per-step failing tests, all 8 migration steps)
- [x] 2.2 Implement (all 8 steps landed green)
- [x] 2.3 Verify (277 pytest + 14 vitest + 3 Playwright e2e; ruff + mypy clean)
- [x] 3.1 Stage (pushed to staging)
- [x] 3.2 Confirm CI (green: Python matrix + frontend + e2e jobs)
- [x] 3.3 Promote (ff-merged to main; all refs at 6349499)

Note: the unit iterated 2.1→2.3 once per migration step (8 steps); the 3.x gates applied per landed step. Two follow-on units (frontend test suite; npm audit 20→0) also completed through 3.3.

Prior unit (senior-review remediation + Step 4.2/4.3 + save/load) completed through 3.3; promoted to `main` at 8ec133c on 2026-06-22.

## Contracts

- 2026-07-04T00:00:00Z · sha256:cde83dbaa90b · docs/architecture-microquiz.md approved by Michael. Amended 2026-07-06 (prose-style pass, semantics unchanged; new sha256:8abdc57a3d45). Predict-and-verify micro-puzzle system: data model, simulator protocol with per-module fidelity statements, five new verbs, difficulty-weighted knowledge meter (cap 5), tiered hints, first-visit auto-prompt, save schema 1.1, eight-step migration plan. Deviations require /prd-amend and re-approval.

_(Decision history predating the schema lives in `decisions.md` and project memory.)_

## Current Plan

**Micro-puzzle system (Direction C, predict-and-verify).** Full blueprint in `docs/architecture-microquiz.md` (decisions resolved 2026-06-26); deep-end minigame design in `docs/design-minigames.md`; research grounding in `mrf-knowledge/game-design/2026-06-22_teaching-games-text-adventure-pivot.md`.

Migration order (each step lands green): **1 simulators ✓ (4a50df1)** → **2 puzzle infra ✓ (4740077)** → **3 player/world wiring ✓ (a816658)** → **4 command surface ✓ (14cddbe)** → **5 content fill ✓ (28/28 puzzles, a510921)** → **6 knowledge-meter cutover ✓ (2252eee)** → **7 minigames consume simulators ✓ (756d910)** → **8 frontend per-room puzzle state ✓ (e08af0f, promoted)**. Microquiz unit COMPLETE.

Step 2 note: puzzles are one-YAML-per-file under `mechanics/puzzles/data/<category>/`, deserialized to frozen `MicroPuzzle` dataclasses, load-time-validated (the registry runs every setup through its named simulator, so a broken puzzle cannot ship). `registry.evaluate(id, raw)` is the single call step 4's commands will use. Three seed puzzles live (two cache, one pipeline). pyyaml is now a runtime dep per contract.

Step 1 note: cache (LRU/FIFO, direct-mapped→fully-associative) and pipeline (stall/forward RAW model) simulators landed with fidelity docstrings; timing conventions (write-through regfile, EX→EX forward, load-use bubble) documented in pipeline.py and pinned by tests (7/8/11 cycle counts). tlb/packet/storage/signature simulators land with their consuming puzzles in step 5.

`tk-a7098e` (4.1 minigames) is DONE: it was steps 1–7 above, all shipped and promoted. Step 4.2's browser verification is DONE (2026-07-03, headless Chromium walkthrough): welcome renders in xterm, typed command flows through the keystroke buffer into Game.feed, terminal prints the move, map re-renders live (Turn 1, current node CPU Package → Core 1). Three defects found and fixed during the walkthrough (d1b51e1). Full-victory playthrough re-verified live (34 turns, all 5 viruses, Victory:true) and the Railway deploy confirmed serving the current bundle.

**Save/load status (not a contradiction):** the Step 1.2 decision (2026-05-02) removed the *placeholder* save/load that silently lost data (99be8ed) and filed a follow-up to reimplement it properly. That follow-up (tk-24fa9f) shipped a real implementation (510ae26). The currently-wired `SaveLoadSystem` plus save/load/deletesave commands are the intended end state. The design docs' "in-flight puzzle/minigame state is not persisted" note is a scoping choice for that feature, not a conflict.

**Deferred features (design-doc "Out of scope"), available if picked up:** author-extensible puzzles, adaptive difficulty (reorder by solve history), higher-fidelity network/security simulators, persistence of in-flight puzzle/minigame state.

**Code-review remediation (2026-07-26) COMPLETE and promoted.** A five-lens
senior/architecture/refactor review ran; Michael approved fixing bugs + cleanup
+ DRY + deploy hardening (NOT the larger structural work). Shipped in four
commits (a43897d, 35abc8a, d0c2c09, efede42): eight bug fixes (B1 web-quit hang,
B2 CHOICE case-sensitivity, B3 all_viruses_found desync, B4-B8 latent/low),
dead-code removal (archive/saveload.py gone, ruff 36 to 0), DRY collapses, and
deploy/security hardening (deploy-safe HOST/CORS defaults, socket input caps).
Test count 277 to 297.

**Structural work COMPLETE and promoted (2026-07-27).** The items previously
deferred were all done in four commits (c1af2f7, bfe5da2, 021a361, 25ea2ae):

- **Content extraction.** Help screen, welcome banner, and the ten component
  articles moved to `computerquest/content/`. A golden fixture
  (`tests/fixtures/golden_content.json`) captured before the move pins the
  output byte-for-byte. `render_welcome()` returns a string, removing the
  stdout-redirect hack in `welcome_text()`.
- **PuzzleSession.** Puzzle orchestration moved to
  `mechanics/puzzles/session.py`; Game delegates and keeps its old attributes
  as properties, so commands.py, save/load, and existing tests are unchanged.
  The puzzle flow is now unit-testable without constructing a Game.
- **Knowledge single-writer.** `apply_reward` could bump `player.knowledge`,
  which the recompute then silently discarded. Rewards are items only now; the
  approved contract defines knowledge as a function of solved puzzles.
- **visited / id-space.** `map_grid` is a derived view over `game_map.rooms`.
  This fixed a LIVE bug: at turn 0 the starting room was visited in map_grid
  but not on the component, so the ASCII map and the React map disagreed (the
  web map showed 0/35 visited when the player was standing in a room).
  Components now carry their rooms-key, so snapshot no longer rebuilds a
  reverse map per call and `current_room_id` is an attribute read. Emitted
  door graph verified byte-identical.

game.py went 1114 -> 703 lines. Tests 297 -> 322. Deployed and verified live.

Follow-on: the win condition now has a real end-to-end playthrough test
(`tests/test_playthrough_victory.py`). The prior victory test mocked out
quarantine and victory_message, so the actual path was never executed. Routes
are BFS-computed, and the test was mutation-checked. Railway was not
redeployed for it: tests and docs only, no runtime change.

**Live victory playthrough (2026-07-28).** Full 26-turn run against production:
all five viruses found and quarantined, MISSION SUCCESSFUL, `game_ended
{victory:true}`. It surfaced two real ASCII-map defects, both fixed in ec630da:

- **The map was non-deterministic.** Overlapping component art was merged in
  set-iteration order, which follows Python's per-process string hash seed, so
  the same game rendered differently between runs (5 runs produced 4 distinct
  outputs). The merge now walks the authored `component_parts` dict. Pinned by
  a test across four PYTHONHASHSEED values.
- **`memory_controller` had no map position**, so it never drew a marker even
  when visited. Same class as the clipped `pcie_x1_2` (B7).

After the fix all three views agree exactly: ASCII markers 11, snapshot
visited 11, React nodes 11. A false alarm was also ruled out during this run:
a low live marker count was a probe artifact (xterm virtualizes its DOM, so an
80-line map only has ~39 rows present), not a product bug.

## Branch & Tests

- Branch: `staging`
- Working tree: clean (aside from this state reconciliation)
- Last CI: green (Python matrix + frontend + e2e) @ ec630da
- `staging` and `main` are in sync at ec630da (all refs, local and origin).
- Tests: 328/328 via `uv run pytest`; ruff clean; mypy clean (required in CI, Python 3.11+3.12 matrix). Frontend: 14 vitest + 3 Playwright e2e green.
- npm audit: 0 vulnerabilities (was 20).
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
- 2026-07-04T00:00:00Z 1.3 → 2.1 microquiz plan approved (sha256:cde83dbaa90b); starting simulator scaffolding

## Narrative history (pre-migration body, condensed)

The senior-developer review (2026-04-19) produced a 26-step remediation plan. All of it shipped: Week 1 critical bugs (hotkey collision, save/load stub removal, minigame gating, server hardening, real-Game test fixtures), Week 2 tooling (pyproject consolidation, version single-sourcing, CI, repo hygiene), Week 3 refactor (game.py split, dead JSON removal, difflib matcher, type annotations, motherboard de-dup, health-bar wiring, constants), Week 4 features (virus-name predicate, NPC pop bug), LP cleanup tail, save/load reimplementation (tk-24fa9f), and Step 4.2 (Game in-process in server.py + GameMap live-state wiring; browser verification pending).

Strategy pivot 2026-06-22: research spike found the game's "knowledge rises with visits" loop sits in the instructionist failed canon. Direction C adopted: keep the exploration shell and make knowledge rise on solved predict-and-verify micro-puzzles checked by real simulators.

- 2026-07-06T00:00:00Z external live-play review: fixed map viewport clamp, two unreachable rooms (door-direction overwrites), node contrast (95b0c60); promoted and redeployed
- 2026-07-06T00:00:00Z microquiz unit COMPLETE through step 8; recorded (a955b6e)
- 2026-07-25T00:00:00Z frontend test-suite unit (vitest + Playwright e2e) landed and promoted (764d973, d7cbf2f)
- 2026-07-25T00:00:00Z npm audit unit: 20 → 0 advisories; vite 5→8, vitest 3→4; promoted (6349499); Railway redeployed and live-verified
- 2026-07-25T00:00:00Z state reconciliation: PROJECT_STATE + tasks.yaml corrected from stale Phase 2.1 to actual shipped state (all refs at 6349499)
- 2026-07-27T00:00:00Z structural refactor shipped: content extraction, PuzzleSession, knowledge single-writer, visited/id-space dedup (c1af2f7..25ea2ae); 318 tests; promoted and redeployed
- 2026-07-28T00:00:00Z live victory playthrough; fixed non-deterministic map render and missing memory_controller marker (ec630da); 328 tests; promoted and redeployed
- 2026-07-26T00:00:00Z code-review remediation shipped: bugs B1-B8, dead-code removal, DRY, deploy hardening (a43897d..efede42); 297 tests; promoted to main
