# PROJECT_STATE — Python-Zork

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Authoritative for "where are we?"; back-up to ephemeral TaskCreate/TaskUpdate.

Last updated: 2026-05-04
Branch: `staging` (plan committed on master; implementation work runs through staging — Week 1, 2, 3 all on staging)

## Current plan summary
Remediation of senior-developer review findings (review run 2026-04-19) for Python-Zork. Plan persisted in [`plan.md`](./plan.md); checklist in [`todo.md`](./todo.md). Work is grouped Week 1 (critical bugs) → Week 2 (build/tooling) → Week 3 (refactor) → Week 4+ (features) plus a low-priority cleanup tail.

## Task checklist with status
All 26 tasks seeded in `tasks.yaml` with dependencies wired. Check task readiness with `/task ready` (shows only unblocked tasks). As of this snapshot, **nothing is started** — the plan was just persisted.

## Last completed step
**Week 3 done — all seven steps (3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7).**

- **Steps 3.6 + 3.7 (tk-df7e06, tk-6caadf)** — Health bar wired to real player; `INVENTORY_LIMIT` and `MAX_HEALTH` centralized in `config.py`. Bundled into commit 86fe99b since both touched the same status-bar code. Dead `hasattr(location, 'game')` branch removed.
- **Step 3.3 (tk-93fa21)** — Replaced custom set-membership similarity with `difflib.get_close_matches(n=3, cutoff=0.6)` (commit 7678cc4). New tests cover near-miss and garbage-input branches.
- **Step 3.2 (tk-04f43c)** — Deleted three dead `data/*.json` files (commit 009f190). Confirmed via grep that no consumer existed in `computerquest/`, `tests/`, `src/`, `server.py`, or `main.py`.
- **Step 3.1 (tk-495cc6)** — Split `game.py`: `ComponentVisualizer` → `mechanics/visualizer.py`, `CPUPipelineMinigame` → `mechanics/minigames/cpu.py`, `MemoryHierarchyMinigame` → `mechanics/minigames/memory.py` (commit 8189d98). game.py shrank 1104 → 833 lines.
- **Step 3.5 (tk-ed93bd)** — De-duplicated motherboard ASCII (commit 8725e17). `ComponentVisualizer.render_motherboard_layout_text` is now the single canonical source; `Game.display_motherboard` delegates. Snapshot test pins landmarks.
- **Step 3.4 (tk-277bbc)** — Backfilled type annotations on `commands.py`, `models/player.py`, `game.py`, `utils/helpers.py` (commit 0f76a71). Per-module mypy override enables `disallow_untyped_defs` and `disallow_incomplete_defs` on those four. CI mypy step flipped from soft-fail to required.

**116/116 tests green; ruff clean; mypy clean.**

Earlier completed: Week 1 (Steps 1.1–1.5, 4.4 + pre-existing test sweep); Week 2 (Steps 2.1–2.4).

## Next step to take
Week 3 done. Week 4 is feature work; remaining tasks per `/task ready`:
- **4.3 (`tk-fe893e`)** add `Component.is_virus` flag; replace `'virus' in target.lower()` string-sniff in `player.py`.
- **4.2 (`tk-7303b8`)** wire React `GameMap.tsx` to live game state via Socket.IO query event (frontend + backend; the biggest remaining task).
- **4.1 (`tk-a7098e`)** implement minigames after design doc; flip `ENABLE_MINIGAMES`. Needs a design doc first.
- Several low-priority cleanup items (LP.1–LP.5).

## Branch and test status
- Active branch at snapshot: `staging`, ahead of `master` by all of Weeks 1 + 2 + 3.
- Tests: **116/116 green.** Plain `uv run pytest` works.
- Lint: ruff clean across `computerquest/` and `tests/`. Required in CI.
- Type-check: **mypy clean across all 18 source files.** Required in CI (no longer soft-fail).
- CI: `.github/workflows/test.yml` runs on push to `staging`/`master`/`main` and on PRs across a Python 3.11+3.12 matrix.
- `tests/_helpers.py::build_real_game` is the canonical test fixture; new tests should use it.
- All four open decisions resolved and saved as project memory: Step 1.2 (REMOVE save/load), Step 1.3 (GATE minigames), Step 3.2 (DELETE data/*.json), Step 3.6 (WIRE health bar to real player).

## Verification method used (for the plan itself)
**Research-based.** The plan was assembled from the static-analysis output of `/review-senior`. No browser, no live test execution against the current branch yet. Per-step verification is defined inline in `plan.md` and is the gate for marking each todo item done.

## What is and is not yet verified
- **Verified by the review (static analysis):** file paths, line numbers, the `s` hotkey collision, the placeholder `SaveLoadSystem`/minigame classes, missing `[project]` table, missing `LICENSE` file, `node_modules/` not in `.gitignore`.
- **NOT yet verified:**
  - That `archive/saveload.py` is portable to current code (gate for Step 1.2 implement path).
  - That no consumer outside `computerquest/` reads `data/*.json` (gate for Step 3.2 delete path; the step's prompt includes an explicit grep check).
  - That every fix lands without behavior regressions — this is what per-step tests + Step 2.3 CI will catch as work progresses.
  - That the existing test suite even runs end-to-end on the current commit (Step 2.1 unblocks this).

## Open decisions awaiting Michael's call
- **Save/load (Step 1.2):** implement now (port from `archive/`) or remove commands and defer. Plan defaults to **remove** + file an issue.
- **Minigames (Step 1.3):** implement now or gate behind `ENABLE_MINIGAMES = False`. Plan defaults to **gate**.
- **`data/*.json` (Step 3.2):** load (cleaner) or delete (smaller surface). Plan defaults to **delete**.
- **Health bar (Step 3.6):** wire to real player or remove cosmetic system. Plan defaults to **wire to real player**.

## Files in this state set
- `plan.md` — full step-by-step blueprint with implementation prompts
- `tasks.yaml` — machine-readable task list with dependencies (26 tasks, all pending)
- `PROJECT_STATE.md` — this file (durable narrative state)
- (Existing `TODO.md`, uppercase, is the **stale** legacy doc — slated for removal in Step LP.1; do not edit it.)
