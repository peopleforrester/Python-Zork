# PROJECT_STATE — Python-Zork

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Authoritative for "where are we?"; back-up to ephemeral TaskCreate/TaskUpdate.

Last updated: 2026-05-04
Branch: `staging` (plan committed on master; implementation work runs through staging)

## Current plan summary
Remediation of senior-developer review findings (review run 2026-04-19) for Python-Zork. Plan persisted in [`plan.md`](./plan.md); checklist in [`todo.md`](./todo.md). Work is grouped Week 1 (critical bugs) → Week 2 (build/tooling) → Week 3 (refactor) → Week 4+ (features) plus a low-priority cleanup tail.

## Task checklist with status
All 26 tasks seeded in `tasks.yaml` with dependencies wired. Check task readiness with `/task ready` (shows only unblocked tasks). As of this snapshot, **nothing is started** — the plan was just persisted.

## Last completed step
**Week 2 done — Steps 2.1, 2.2, 2.3, 2.4.**

- **Step 2.1 (tk-80ec19)** — Packaging consolidated into a single `pyproject.toml` `[project]` table (commit 151039f). `setup.py`, `setup.cfg`, `requirements.txt` deleted. uv.lock committed. ruff replaces black/isort/flake8/pylint. Makefile uses uv. LICENSE created (MIT, Michael Forrester, 2026). `uv run pytest` works directly — workaround retired.
- **Step 2.2 (tk-b78acd)** — Version drift resolved (commit 2c82bd7). `computerquest.__version__` derives from `importlib.metadata.version("computerquest")`; `config.GAME_VERSION` mirrors. Bumped to 1.1.1 to mark the Week-1 critical-bug shipment. `tests/test_version.py` pins the contract.
- **Step 2.3 (tk-d34e62)** — CI workflow added at `.github/workflows/test.yml` (commit f093274) — Python 3.11 + 3.12 matrix, uv setup, lock-honoring sync, ruff (required), mypy (soft-fail until 3.4), pytest with coverage. Codebase ruff-clean: 899 → 0 errors via auto-fix + targeted manual cleanup.
- **Step 2.4 (tk-0e834b)** — Repo hygiene (commit 409c218). `node_modules/`, `.vite/`, `*.tsbuildinfo` gitignored; 3171 stale frontend files untracked from the index. README Python min bumped 3.8 → 3.10, Node min 14 → 18 (Vite 5 requirement), install steps switched to `uv sync --dev`.

**110/110 tests green; ruff clean.** Both Week 1 (critical bugs) and Week 2 (build/tooling) are complete.

Earlier completed: Week 1 critical bugs (Steps 1.1–1.5, 4.4) plus the pre-existing test sweep.

## Next step to take
Week 2 done. Week 3 (refactor) is next. Most Week-3 tasks are independent and can be parallelized:
- **3.2 (`tk-04f43c`)** decide on `data/*.json` (default per plan: delete unless Michael says load).
- **3.3 (`tk-93fa21`)** replace fuzzy matcher with `difflib.get_close_matches`.
- **3.6 (`tk-df7e06`)** wire the dead health-bar `hasattr` branch to the real player.
- **3.7 (`tk-6caadf`)** centralize `INVENTORY_LIMIT = 8` and other shared literals in `config.py`.
- **3.1 (`tk-495cc6`)** split `game.py` (1035 lines → mechanics/) — biggest refactor; touches every minigame/visualizer/save reference. Should be done before 3.4 (mypy) and 3.5 (motherboard de-dup).
- **3.4 (`tk-277bbc`)** backfill type annotations and flip mypy to required (depends on 3.1 + 2.3).
- **3.5 (`tk-ed93bd`)** de-duplicate motherboard ASCII (depends on 3.1).

## Branch and test status
- Active branch at snapshot: `staging`, ahead of `master` by all of Week 1 + Week 2.
- Tests: **110/110 green.** Plain `uv run pytest` works (Step 2.1 retired the `--no-project --with` workaround).
- Lint: ruff clean across `computerquest/` and `tests/`. Required in CI.
- Type-check: mypy is wired into CI but soft-fails until Step 3.4.
- CI: `.github/workflows/test.yml` runs on push to `staging`/`master`/`main` and on PRs. Python 3.11+3.12 matrix, uv setup, lock-honoring sync.
- `tests/_helpers.py::build_real_game` is the canonical test fixture; new tests should use it.
- Open decisions resolved: Step 1.2 (REMOVE save/load) and Step 1.3 (GATE minigames) — both saved as project memory. Steps 3.2 (data/*.json: default delete) and 3.6 (health bar: default wire to real player) still need Michael's call when those steps come up.

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
