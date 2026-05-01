# PROJECT_STATE — Python-Zork

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Authoritative for "where are we?"; back-up to ephemeral TaskCreate/TaskUpdate.

Last updated: 2026-05-02
Branch: `staging` (plan committed on master; implementation work runs through staging)

## Current plan summary
Remediation of senior-developer review findings (review run 2026-04-19) for Python-Zork. Plan persisted in [`plan.md`](./plan.md); checklist in [`todo.md`](./todo.md). Work is grouped Week 1 (critical bugs) → Week 2 (build/tooling) → Week 3 (refactor) → Week 4+ (features) plus a low-priority cleanup tail.

## Task checklist with status
All 26 tasks seeded in `tasks.yaml` with dependencies wired. Check task readiness with `/task ready` (shows only unblocked tasks). As of this snapshot, **nothing is started** — the plan was just persisted.

## Last completed step
**Week 1 critical bugs done — Steps 1.2, 1.3, 1.4 (commits 99be8ed, 1cdddf6, +server hardening).**

- **Step 1.2 (tk-766699)** — Save/load surface removed (commit 99be8ed). SaveLoadSystem class, four save/load commands, unsaved-changes prompts in QuitCommand and the game loop, save/load help text and README advertisement all gone. Follow-up `tk-24fa9f` filed for porting `archive/saveload.py` later.
- **Step 1.3 (tk-efa52e)** — Minigames gated behind `config.ENABLE_MINIGAMES = False` (commit 1cdddf6). SimulateCommand short-circuits cpu/memory branches when off. Placeholder classes retained; Step 4.1 only needs to flip the flag.
- **Step 1.4 (tk-71d733)** — server.py hardened. Env-driven CORS (`CQ_CORS_ORIGINS`, default `http://localhost:5173`), `CQ_DEBUG` defaults False, `CQ_HOST` defaults `127.0.0.1`, bare `except:` replaced with `ProcessLookupError` + logging, `_terminate_game_process()` cleans up on disconnect AND atexit, Python interpreter resolved via `sys.executable`. README documents env vars and the security caveat. New `tests/test_server.py` covers the env helpers.

**107/107 tests green.** All five Week-1 critical tasks (1.1, 1.2, 1.3, 1.4, 1.5) plus Step 4.4 are done.

Earlier completed: pre-existing test sweep / Step 4.4 (0ba21e4); Step 1.5 (1747446) — real-Game fixtures; Step 1.1 (7578ede) — `s` hotkey collision.

## Next step to take
Week 1 done. Remaining ready tasks (`/task ready`) span Week 2 (build/tooling) and onward. Recommended order: **2.1 (`tk-80ec19`)** consolidate packaging into `pyproject.toml [project]` — unblocks `uv run pytest` (currently requires the `--no-project --with` workaround) and is a prerequisite for 2.2 and 2.3. Then **2.4 (`tk-0e834b`)** lightweight repo hygiene (`.gitignore`, LICENSE, README Node version). Then 2.2 / 2.3 in either order.

## Branch and test status
- Active branch at snapshot: `staging`, ahead of `master` by all critical-bug fixes plus Step 1.4.
- Tests: **107/107 green.** `uv run pytest` still fails because `pyproject.toml` has no `[project]` table (Step 2.1). Workaround for now: `PYTHONPATH=. uv run --no-project --with pytest --with pytest-cov --with flask --with flask-socketio --with flask-cors pytest <path>` (the flask deps are needed since `tests/test_server.py` imports `server`).
- `tests/_helpers.py::build_real_game` is the canonical test fixture; new tests should use it.
- CI: none yet (Step 2.3).
- Open decisions resolved: Step 1.2 (REMOVE save/load — saved as project memory); Step 1.3 (GATE minigames — saved as project memory). Steps 3.2 (data/*.json) and 3.6 (health bar) still have plan-default decisions awaiting Michael's confirmation when those steps come up.

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
