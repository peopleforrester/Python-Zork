# PROJECT_STATE — Python-Zork

ABOUTME: Durable state record for /continue. Updated at every transition.
ABOUTME: Authoritative for "where are we?"; back-up to ephemeral TaskCreate/TaskUpdate.

Last updated: 2026-05-25
Branch: `staging` (plan committed on master; implementation work runs through staging — Weeks 1-3, Step 4.3, and the LP cleanup tail all on staging)

## Current plan summary
Remediation of senior-developer review findings (review run 2026-04-19) for Python-Zork. Plan persisted in [`plan.md`](./plan.md); checklist in [`todo.md`](./todo.md). Work is grouped Week 1 (critical bugs) → Week 2 (build/tooling) → Week 3 (refactor) → Week 4+ (features) plus a low-priority cleanup tail.

## Task checklist with status
All 26 tasks seeded in `tasks.yaml` with dependencies wired. Check task readiness with `/task ready` (shows only unblocked tasks). As of this snapshot, **nothing is started** — the plan was just persisted.

## Last completed step
**Step 4.3 + LP cleanup tail done (commits f55313c, 29021cb).**

- **Step 4.3 (tk-fe893e)** — `config.is_virus_name()` replaces `'virus' in name.lower()` substring matching across five sites in `player.py`. Backed by `frozenset(VIRUS_TYPES)`. Test fixtures `virus_item`, `antivirus_tool`, `test_virus` no longer false-positive. The description-content heuristics (`suspicious`/`malicious` in desc) are intentionally retained.
- **LP.1 (tk-90845e)** — Removed `IMPROVEMENTS.md`, uppercase `TODO.md`, and 11 of 12 `archive/` files. Kept `archive/saveload.py` because `tk-24fa9f` references it as the future-port source.
- **LP.2 (tk-5fe152)** — `Colors` attributes guarded by `sys.stdout.isatty()`; captured/piped output gets empty strings, not ANSI escapes.
- **LP.3 (tk-fc8e15)** — `ClearCommand` and game loop write `\x1b[2J\x1b[H` on a TTY; no-op otherwise. No more `os.system` fork per command.
- **LP.4 (tk-3ee2e9)** — README clone URL points to `peopleforrester/Python-Zork`.
- **LP.5 (tk-f0d6b8)** — Closed retroactively; already satisfied by commit 86fe99b's welcome rewrite.

**120/120 tests green; ruff + mypy clean.**

Earlier completed: Weeks 1–3 (Steps 1.1–1.5, 2.1–2.4, 3.1–3.7), Step 4.4 (NPC pop bug), pre-existing test sweep.

## Next step to take
The senior-review remediation is effectively complete. Three feature tasks remain — all genuine new development, not review remediation:

- **tk-24fa9f** — Port `archive/saveload.py` into a real save/load implementation. Most concrete of the three (reference impl already in repo). The decision memory authorizes this as the "implement later" follow-up to Step 1.2's removal.
- **tk-7303b8 (4.2)** — Wire React `GameMap.tsx` to live game state via a new Socket.IO `query_state` event. Substantial: needs schema design, server changes, frontend rewrite, browser verification.
- **tk-a7098e (4.1)** — Implement CPU pipeline + memory hierarchy minigames. Genuinely speculative without a design doc; the plan calls for `docs/design-minigames.md` as pre-work.

## Branch and test status
- Active branch at snapshot: `staging`, ahead of `master` by Weeks 1+2+3 plus Step 4.3 and the LP tail.
- Tests: **120/120 green.** Plain `uv run pytest` works.
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
