# PROJECT_STATE — Python-Zork

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Authoritative for "where are we?"; back-up to ephemeral TaskCreate/TaskUpdate.

Last updated: 2026-05-01
Branch: `staging` (plan committed on master; implementation work runs through staging)

## Current plan summary
Remediation of senior-developer review findings (review run 2026-04-19) for Python-Zork. Plan persisted in [`plan.md`](./plan.md); checklist in [`todo.md`](./todo.md). Work is grouped Week 1 (critical bugs) → Week 2 (build/tooling) → Week 3 (refactor) → Week 4+ (features) plus a low-priority cleanup tail.

## Task checklist with status
All 26 tasks seeded in `tasks.yaml` with dependencies wired. Check task readiness with `/task ready` (shows only unblocked tasks). As of this snapshot, **nothing is started** — the plan was just persisted.

## Last completed step
**Step 1.5 — Real-Game test fixtures (committed on staging, commit 1747446).** Replaced MagicMock-heavy `setUp` in `tests/test_commands.py` and `tests/test_game.py` with a `build_real_game()` builder in `tests/_helpers.py`. Identity-function lambdas removed; real prefix matchers exercised by every command test. Narrow `patch.object` used where a specific method's return value still needs to be controlled. **59 tests green (37 commands + 22 game).** Filed `tk-5dea92` for 10 pre-existing failures in `test_architecture` / `test_helpers` / `test_player` / `test_progress`.

Earlier completed: Step 1.1 — `s` hotkey collision (commit 7578ede).

## Next step to take
Push `staging` to `origin/staging`, then pick the next unblocked critical task from `/task ready`. Remaining Week-1 candidates: **1.2** (save/load — decision needed), **1.3** (minigame stubs — decision needed), **1.4** (server.py hardening — independent). Recommended order: 1.4 first since it has no open decisions and is purely defensive; 1.2 and 1.3 next once you've called the implement-vs-remove / implement-vs-gate decisions.

## Branch and test status
- Active branch at snapshot: `staging` (3 commits ahead of `master` after Step 1.5: 7578ede, 3d39057, 1747446).
- Tests: `uv run pytest` still fails because `pyproject.toml` has no `[project]` table (Step 2.1). Workaround in use: `PYTHONPATH=. uv run --no-project --with pytest --with pytest-cov pytest <path>`.
- Step-1.5 scope (test_commands.py + test_game.py): 59/59 green. `tests/_helpers.py::build_real_game` is the canonical test fixture; new tests should use it.
- Out-of-scope: 10 pre-existing failures in test_architecture / test_helpers / test_player / test_progress remain — tracked as `tk-5dea92`.
- CI: none yet (Step 2.3).

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
