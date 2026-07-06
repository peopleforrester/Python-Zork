# Python-Zork Remediation Plan

ABOUTME: Step-by-step implementation blueprint derived from the senior developer review.
ABOUTME: Each step is right-sized for one branch/PR; mark progress in todo.md and PROJECT_STATE.md.

**Source:** `/review-senior` output, 2026-04-19
**Owner:** Michael
**Branch policy:** all work on `staging`, merged to `main` only after tests pass
**Verification method for this plan:** static analysis from review output; per-step verification is defined inline (tests / manual / browser)

---

## How to use this plan

1. Pick the next un-checked step in `todo.md`.
2. `git checkout staging && git pull origin staging` (create from `main` if missing).
3. Follow the step's prompt; satisfy the exit criteria; run verification.
4. Commit, push to `staging`. Only after CI/tests pass, merge to `main`.
5. Update `todo.md` and `PROJECT_STATE.md` (last-completed / next-up / verification status).

Steps are grouped by week to match the review's recommended cadence, but each step is independent and can be reordered if a higher-priority bug surfaces.

---

# Week 1. Critical Bugs

## Step 1.1. Fix `s` hotkey collision (south vs scan)

**Scope:** the `self.commands` dict in `computerquest/commands.py` binds key `'s'` twice (line 432 → south, line 460 → `ScanCommand`). Python keeps the last value, so `s` invokes Scan and documented south movement is broken.

**Files touched:**
- `computerquest/commands.py` (rebind one of the two)
- `computerquest/game.py:711` and any other in-game help text advertising `s`
- `README.md:86` if the rebind changes the public hotkey
- `tests/test_commands.py` (new regression test)

**Implementation prompt:**
```text
In computerquest/commands.py, the dict literal at self.commands binds 's' to
_direction_command('south') and again to ScanCommand. Resolve the collision by
keeping 's' as south (matches README and in-game help) and rebinding scan to
'sc' (with 'scan' still available as the long form). Update help text in
commands.py:385, game.py:711, and any other in-game help string advertising scan.

Add tests/test_commands.py::test_s_resolves_to_south and
::test_sc_resolves_to_scan that look up the resolved command class via the
real CommandProcessor (no MagicMock) and assert the type. Tests must fail
against the current code and pass after the fix.
```

**Verification:**
- New tests fail before, pass after.
- `uv run pytest tests/test_commands.py -k hotkey` green.
- Manual: launch game, press `s` from a room with a south exit and confirm movement.

**Exit criteria:** `s` moves south; `sc` and `scan` invoke scan; help text consistent across README, `help`, and `quickhelp`; regression test committed.

---

## Step 1.2. Decide on save/load: implement or remove

**Scope:** `SaveLoadSystem` (`computerquest/game.py:266-281`) is a no-op. `SaveCommand`, `LoadCommand`, `SavesCommand`, `DeleteSaveCommand` are wired up and the quit flow prompts to "save before exit". Users lose data silently.

**Decision required:** implement (port `archive/saveload.py`) OR remove the commands and the unsaved-changes prompt. Default recommendation: **remove** for now and file an issue to implement later; that keeps the surface honest.

**Files touched (remove path):**
- `computerquest/game.py`: delete `SaveLoadSystem` class and the quit-flow prompt
- `computerquest/commands.py`: remove the four save/load command classes and their dict registrations
- `tests/`: drop any tests asserting save/load behavior; add a test that `save` is unknown
- `README.md`: strike save/load from feature list
- New GitHub issue: "Implement persistent save/load (port from archive/saveload.py)"

**Files touched (implement path):**
- `computerquest/mechanics/save_load.py` (new, ported from `archive/saveload.py`)
- `computerquest/game.py`: replace stub with import
- `tests/test_save_load.py` (new) covering round-trip serialize/deserialize, error on missing save, list/delete

**Implementation prompt (remove):**
```text
Remove the SaveLoadSystem placeholder and its commands. In game.py delete the
SaveLoadSystem class (lines 266-281) and any references in the quit flow that
ask the user about unsaved changes. In commands.py remove SaveCommand,
LoadCommand, SavesCommand, DeleteSaveCommand and their entries in self.commands.
Update README and in-game help to no longer advertise save/load. Add a regression
test asserting `save` resolves to the unknown-command path. Open a GitHub
issue titled "Implement persistent save/load (port from archive/saveload.py)"
and link archive/saveload.py.
```

**Verification:** `uv run pytest`; manual quit flow no longer prompts; `save` returns unknown command.

**Exit criteria:** code matches advertised behavior; issue filed if implementation is deferred.

---

## Step 1.3. Decide on minigames: implement or feature-flag

**Scope:** `CPUPipelineMinigame` (`game.py:240-257`) and `MemoryHierarchyMinigame` (`game.py:259-264`) return placeholder strings. `simulate cpu` / `simulate memory` are user-visible.

**Decision required:** implement OR hide behind `config.ENABLE_MINIGAMES = False`. Default: **hide** until designed.

**Files touched (hide path):**
- `computerquest/config.py`: add `ENABLE_MINIGAMES: bool = False`
- `computerquest/commands.py`: `SimulateCommand.execute()` returns "Minigames not yet available." when the flag is off
- `tests/test_commands.py`: assert the gated behavior

**Implementation prompt:**
```text
Add ENABLE_MINIGAMES = False to computerquest/config.py. Modify the simulate
command in commands.py so that when the flag is False, both `simulate cpu` and
`simulate memory` return "Minigames are not yet available, track progress in
issue #N." When the flag is True, the existing knowledge-gated stubs run.
Add tests asserting both branches. Do NOT delete the placeholder classes -
leave them so the implement-path step can flesh them out (Week 4 step 4.1).
```

**Verification:** new test green; manual `simulate cpu` returns the disabled message.

**Exit criteria:** users no longer hit "placeholder" output; flag flip is the single switch when implementation lands.

---

## Step 1.4. Harden `server.py`

**Scope:** allow-all CORS, `debug=True`, `0.0.0.0` bind, per-connection `subprocess.Popen(["python", "main.py"])` with no auth, bare `except:` at lines 36 and 65, no orphan-process cleanup.

**Files touched:**
- `server.py`
- `requirements.txt` / `pyproject.toml` if a new dep is needed
- `README.md` (deployment section)

**Implementation prompt:**
```text
Harden server.py for at least dev safety:

1. Read CORS origins from env CQ_CORS_ORIGINS (comma-separated); default to
   ["http://localhost:5173"]. Apply to both flask_cors.CORS and SocketIO.
2. Default debug=False; only enable when env CQ_DEBUG=1.
3. Default host="127.0.0.1"; allow override via CQ_HOST.
4. Replace bare `except:` at lines 36 and 65 with `except ProcessLookupError:`
   (or the actual expected exception) and log via the logging module.
5. Track spawned subprocesses in a dict keyed by sid; on disconnect AND on
   shutdown (atexit handler), terminate and wait() each one.
6. Resolve the python interpreter via sys.executable, not bare "python".
7. Document the env vars and the security caveat ("multi-user is not
   supported; do not expose to the internet") in README.md.

Do not introduce auth in this step, that is a separate feature.
```

**Verification:**
- Manual: `CQ_DEBUG=1 python server.py` starts in debug, default does not.
- Manual: connect from disallowed origin → blocked.
- Manual: kill browser tab → child python exits within 2 s.
- Add a unit test asserting the env-var parser returns the expected list.

**Exit criteria:** no wildcard CORS, no debug-by-default, no orphan processes after disconnect, no bare except.

---

## Step 1.5. Replace identity-function test mocks

**Scope:** `tests/test_commands.py:55-57` patches `_match_item_prefix` and `_match_command_prefix` to identity lambdas and replaces `self.game` with `MagicMock`. `tests/test_game.py:18-50` patches `ComputerArchitecture.setup` and replaces `player`/`game_map` with `MagicMock`. The tests assert behavior of the very methods they stub, hiding bugs (including the `s` hotkey collision).

**Files touched:**
- `tests/test_commands.py`
- `tests/test_game.py`
- possibly a new `tests/conftest.py` with a real-fixtures factory

**Implementation prompt:**
```text
Refactor tests/test_commands.py and tests/test_game.py to exercise real
collaborators:

1. Build a real Game instance in a pytest fixture (conftest.py) using the
   actual ComputerArchitecture, Player, and CommandProcessor. Seed it with a
   small deterministic world (or the real one, whichever runs in <100ms).
2. Remove the lambda overrides of _match_item_prefix / _match_command_prefix.
   Assertions should now exercise the real prefix-matcher.
3. Remove MagicMock substitutions of self.game.player and self.game.game_map
   in test_game.py. If a specific scenario needs a stub, narrow the patch to
   the exact method, not the whole object.
4. Re-run the suite. Note any newly-revealed bugs in todo.md as their own
   steps; do not fix them in this PR.
```

**Verification:** `uv run pytest` runs; failing tests due to real-method exposure get filed as new todo items. Coverage for `commands.py` should increase.

**Exit criteria:** no MagicMock at module scope in either file; no identity-function method overrides; suite still runnable (even if some real bugs now fail and become new tickets).

---

# Week 2. Build & Tooling

## Step 2.1. Consolidate packaging into `pyproject.toml`

**Scope:** `pyproject.toml` lacks a `[project]` table, so `uv sync` / `uv run pytest` (advertised in `CLAUDE.md`) fails. Metadata is split across `setup.py`, `setup.cfg`, `requirements.txt`.

**Files touched:**
- `pyproject.toml` (add `[project]`, `[project.optional-dependencies]`, `[build-system]`)
- delete `setup.py` and `setup.cfg` if pyproject covers them
- `requirements.txt` (delete or convert to a uv-export)
- `Makefile:44-46` (drop the `pip install -e ".[dev]"` line in favor of `uv sync --dev`)
- `CLAUDE.md` (verify `uv run pytest` now works)

**Implementation prompt:**
```text
Migrate Python-Zork to a single source of truth in pyproject.toml.

1. Add [project] with name, version (sourced from a single constant, see
   step 2.2), description, requires-python, dependencies (from
   requirements.txt and setup.py install_requires), readme, license.
2. Add [project.optional-dependencies] with `dev` from setup.py extras_require
   plus pytest, pytest-cov, ruff, mypy.
3. Add [project.scripts] for the CLI entry point if applicable.
4. Add [build-system] using hatchling (or whatever matches existing layout).
5. Delete setup.py and setup.cfg.
6. Replace requirements.txt with a comment pointing to pyproject + uv.lock
   (or remove entirely if no consumer references it).
7. Run `uv sync --dev` and `uv run pytest`. Commit uv.lock.
8. Update Makefile install target to use uv.

CLAUDE.md should now match reality.
```

**Verification:** clean `uv sync --dev && uv run pytest` from a fresh checkout.

**Exit criteria:** one packaging file, lockfile committed, advertised commands work.

---

## Step 2.2. Resolve version drift

**Scope:** `computerquest/__init__.py` says `1.1.0`, `config.py:9` says `1.0.0`, `setup.cfg` says `1.1.0`.

**Files touched:**
- `computerquest/__init__.py`
- `computerquest/config.py`
- `pyproject.toml`

**Implementation prompt:**
```text
Pick pyproject.toml's [project].version as the single source. In
computerquest/__init__.py and config.py, derive __version__ /
GAME_VERSION via importlib.metadata.version("computerquest") with a
PackageNotFoundError fallback that reads from a sentinel constant only
during local dev. Bump to the next patch (1.1.1) since the merge ships
behavior changes from Week 1.
```

**Verification:** `python -c "import computerquest; print(computerquest.__version__)"` matches `pyproject.toml`.

**Exit criteria:** one version string project-wide.

---

## Step 2.3. Add CI workflow

**Scope:** no automated tests on push.

**Files touched:** `.github/workflows/test.yml` (new)

**Implementation prompt:**
```text
Create .github/workflows/test.yml that:

1. Triggers on push to staging and main, and on pull_request.
2. Uses ubuntu-latest, python 3.11 and 3.12 matrix.
3. Installs uv via astral-sh/setup-uv@v3.
4. Runs `uv sync --locked --dev`, `uv run ruff check .`,
   `uv run mypy src/` (allowed to soft-fail until step 3.4 lands),
   `uv run pytest --cov=computerquest`.
5. Uploads coverage as an artifact.

Do not add a deploy job.
```

**Verification:** push the branch, confirm green check on staging.

**Exit criteria:** CI runs and gates merges.

---

## Step 2.4. Repo hygiene: `.gitignore`, `LICENSE`, README Node version

**Scope:**
- `node_modules/` is **not** in `.gitignore` (verified by review).
- README and `setup.py` claim MIT but no `LICENSE` file ships.
- README says Node 14, but Vite 5 requires Node 18+.

**Files touched:** `.gitignore`, `LICENSE` (new), `README.md`

**Implementation prompt:**
```text
1. Append `node_modules/` and `dist/` and `.vite/` to .gitignore. Run
   `git rm --cached -r node_modules` if it is currently tracked.
2. Add an MIT LICENSE file with Michael as the copyright holder
   (year 2026).
3. README: bump Node minimum to 18 (Vite 5 requirement). Update any other
   stale install instructions.
```

**Verification:** `git status` clean of node_modules; `git ls-files | grep node_modules` empty; README install steps reproducible from a fresh box.

**Exit criteria:** repo is buildable from README instructions on a current LTS node.

---

# Week 3. Refactor

## Step 3.1. Split `game.py`

**Scope:** `game.py` is 1035 lines and bundles `Game`, `ComponentVisualizer` (237 lines), `CPUPipelineMinigame`, `MemoryHierarchyMinigame`, `SaveLoadSystem`. The package already has an empty `mechanics/minigames/` subpackage waiting.

**Files touched:**
- `computerquest/mechanics/visualizer.py` (new, takes `ComponentVisualizer`)
- `computerquest/mechanics/minigames/cpu.py` (new)
- `computerquest/mechanics/minigames/memory.py` (new)
- `computerquest/mechanics/save_load.py` (new, only if step 1.2 chose the implement path; otherwise this sub-step is dropped)
- `computerquest/game.py` (imports + slimmer `Game` class only)
- tests updated for new import paths

**Implementation prompt:**
```text
Split game.py without changing behavior. Move:
- ComponentVisualizer → computerquest/mechanics/visualizer.py
- CPUPipelineMinigame → computerquest/mechanics/minigames/cpu.py
- MemoryHierarchyMinigame → computerquest/mechanics/minigames/memory.py
- SaveLoadSystem → computerquest/mechanics/save_load.py (if still present)

Update game.py to import from the new modules. Update mechanics/__init__.py
to re-export the public symbols. Verify with grep that no old paths remain.
Run the full test suite, behavior must not change.
```

**Verification:** `uv run pytest` green; `wc -l computerquest/game.py` < 600.

**Exit criteria:** no class definitions in `game.py` other than `Game` itself; mechanics subpackage populated.

---

## Step 3.2. Decide on `data/*.json`

**Scope:** `data/component_data.json`, `items_data.json`, `virus_data.json` are never read; `architecture.py::make_components()` is the live source. Drift risk.

**Decision:** delete (default) OR migrate `make_components` to load from JSON.

**Implementation prompt (delete path):**
```text
Confirm via grep that no code in computerquest/, server.py, or src/ reads
data/component_data.json / items_data.json / virus_data.json. Delete the
three files and the data/ directory if empty. Add a section to
docs/architecture.md noting that components are defined imperatively in
architecture.py::make_components().
```

**Verification:** `grep -r component_data.json` returns nothing; tests still pass.

**Exit criteria:** one source of truth for component data.

---

## Step 3.3. Replace fuzzy matcher with `difflib.get_close_matches`

**Scope:** `commands.py:583-589` uses `sum(c in command for c in cmd)` (set-membership, not edit distance). Misranks short candidates.

**Files touched:** `computerquest/commands.py`, `tests/test_commands.py`

**Implementation prompt:**
```text
Replace the hand-rolled similar-command suggester in commands.py:583-589
with difflib.get_close_matches(command, self.commands.keys(), n=3, cutoff=0.6).
Add tests covering: exact match returns 0 suggestions (or skips the suggester
entirely), typo "movee" → "move" suggested, garbage input returns empty.
```

**Verification:** new tests green; manual typo run-through.

**Exit criteria:** no custom string-similarity loop remains.

---

## Step 3.4. Backfill type annotations

**Scope:** project-wide grep returned zero hint markers in `computerquest/*.py`. Global rule requires annotations on new code; mypy is configured but has nothing to check.

**Files touched (priority order):**
- `computerquest/commands.py`
- `computerquest/models/player.py`
- `computerquest/game.py`
- `computerquest/utils/helpers.py`
- enable strict-ish `mypy` over `computerquest/`

**Implementation prompt:**
```text
Add type annotations to commands.py, models/player.py, game.py, and
utils/helpers.py. Use only stable types (no Self until py3.11+ baseline is
confirmed). Tighten mypy config in pyproject.toml: enable `disallow_untyped_defs`
for these four modules via per-module overrides. Run `uv run mypy
computerquest/` and address findings in the same PR.

Do NOT alter behavior. If a type reveals a bug, file a new todo item and
keep the annotation truthful (use `# type: ignore[...]` with a reason
sparingly).
```

**Verification:** `uv run mypy computerquest/commands.py computerquest/models/player.py computerquest/game.py computerquest/utils/helpers.py` clean.

**Exit criteria:** four target modules pass strict mypy; CI mypy step (Step 2.3) flips from soft-fail to required.

---

## Step 3.5. De-duplicate ASCII motherboard diagrams

**Scope:** `game.py:910-976` and `game.py:194-238` (inside `ComponentVisualizer.render_motherboard_layout_text`) both render motherboard diagrams.

**Files touched:** `computerquest/mechanics/visualizer.py` (post-3.1) or `game.py`

**Implementation prompt:**
```text
Diff the two motherboard diagrams. Pick the more accurate one, delete the
other, and route both call sites to the survivor. Add a unit test that calls
the renderer once and snapshot-asserts a known substring (e.g., "CPU") so
future edits stay in one place.
```

**Verification:** snapshot test green; second call site re-renders identically by inspection.

**Exit criteria:** one motherboard renderer in the codebase.

---

## Step 3.6. Remove dead health-bar branch

**Scope:** `helpers.py:296-303` checks `hasattr(location, 'game') and hasattr(location.game, 'player')` but `Component` has no `game` attribute. Falls through to hard-coded `max_health = 20`. `game.py:540-546` has a parallel dead branch with a `# placeholder` comment.

**Files touched:** `computerquest/utils/helpers.py`, `computerquest/game.py`

**Implementation prompt:**
```text
The health bar in helpers.format_look_output() and game.py:540 always falls
through to the hardcoded defaults because Component has no `game` attribute.

Decide:
(a) Pass `player` explicitly into format_look_output(location, player=...) and
    read max/current health from the player. Update both call sites.
(b) Delete the health bar entirely if health is not a real mechanic
    (review noted "health system is effectively cosmetic").

Default: (a). Read from self.player. Remove `# placeholder` comments. Add a
unit test that bumps player.health and asserts the rendered status reflects
it.
```

**Verification:** new test green; manual: a damaged player shows reduced health in the status line.

**Exit criteria:** no dead `hasattr` branch; no `# placeholder` comment in this code path.

---

## Step 3.7. Centralize magic numbers

**Scope:** inventory limit `8` hard-coded at `player.py:120` and `helpers.py:321`.

**Files touched:** `computerquest/config.py`, `models/player.py`, `utils/helpers.py`

**Implementation prompt:**
```text
Add INVENTORY_LIMIT = 8 to config.py. Replace the literal 8 in player.py:120
and helpers.py:321 with the constant. While you're there, audit nearby
literals (max health 20, etc.) and lift any that are referenced in more than
one place.
```

**Verification:** grep for the literal `8` in those files returns no inventory references; tests pass.

**Exit criteria:** one constant per cross-cutting limit.

---

# Week 4+. Features

## Step 4.1. Implement minigames (or remove entirely)

**Scope:** flip `ENABLE_MINIGAMES` from Step 1.3 once `CPUPipelineMinigame` and `MemoryHierarchyMinigame` are real. This is a design step, not a refactor, out of scope to spec here without a design doc.

**Pre-work:** write `docs/design-minigames.md` with educational objectives, learning loops, and interactive surface.

**Exit criteria:** `simulate cpu` and `simulate memory` deliver a teaching experience that maps to a stated learning objective; flag flips on.

---

## Step 4.2. Wire React `GameMap.tsx` to live game state

**Scope:** frontend currently shows 5 hard-coded nodes with `Math.random()` status on a 5-second interval. There is no game-state API, frontend is xterm.js piping over Socket.IO to a forked `python main.py`.

**Sub-steps:**
1. Add a `GameState` query event over Socket.IO that the Python side responds to with a JSON snapshot (current room, components visible, virus locations discovered, inventory, achievements). Define the schema in `docs/api-gamestate.md`.
2. In `src/components/GameMap.tsx`, replace the sample data and `Math.random()` interval with a Socket.IO subscription.
3. Render all 30+ components, not just 5.
4. Remove the `// This would be a real API call in production` TODO at line 62.
5. Browser-test (Puppeteer or manual): move in CLI, watch map update.

**Exit criteria:** map reflects real game state; no `Math.random()` in component status; documented schema.

---

## Step 4.3. Replace virus string-sniffing with a flag

**Scope:** `player.py:172`, `:191`, `:298` do `'virus' in target.lower()`.

**Files touched:** `computerquest/world/component.py` (or wherever `Component` is defined), `computerquest/models/player.py`, world/architecture seed data

**Implementation prompt:**
```text
Add `is_virus: bool = False` to the Component class. Set it on the appropriate
components at construction in architecture.py::make_components(). Replace each
`'virus' in target.lower()` check in player.py with `target.is_virus`. Add a
test that creates a non-virus component named "antivirus_tool" and asserts it
is NOT detected as a virus (current code would false-positive).
```

**Verification:** new test fails before, passes after.

**Exit criteria:** no string-sniffing of "virus"; localizable.

---

## Step 4.4. Fix latent NPC pop bug

**Scope:** `player.py:58` calls `self.location.play.append(room.play.pop(self))`. `list.pop()` takes int. Dead path today (no NPCs go through this), latent crash if one ever does.

**Files touched:** `computerquest/models/player.py`, `tests/test_player.py`

**Implementation prompt:**
```text
Fix player.py:58. Replace `room.play.pop(self)` with `room.play.remove(self)`
followed by an append, OR refactor to a single list operation. Add a unit
test that constructs an NPC, places it in a room, calls go() to move it,
and asserts both rooms' .play lists reflect the move. The current code
raises TypeError on this test.
```

**Verification:** new test fails before, passes after.

**Exit criteria:** NPC movement no longer crashes.

---

# Low-priority cleanup (do opportunistically)

## Step LP.1. Remove stale planning docs and `archive/`
Delete or relocate `IMPROVEMENTS.md`, `TODO.md` (uppercase, the stale one), and `archive/` once Week 1–3 work is merged. Confirm no live code imports `archive/`.

## Step LP.2. Guard ANSI colors with `sys.stdout.isatty()`
In the `Colors` constants module, wrap all escape sequences so they emit empty strings when not a TTY. Add a test using `capsys` with `monkeypatch.setattr("sys.stdout.isatty", lambda: False)`.

## Step LP.3. Replace `os.system('clear')` with direct escape codes
Use `sys.stdout.write('\033[2J\033[H')` and `sys.stdout.flush()`. Skip when not a TTY (composes with LP.2). Avoids spawning a shell.

## Step LP.4. Fix README/`setup.py` upstream URLs
Replace `https://github.com/yourusername/...` and `kodekloud/computer-quest` placeholders with Michael's actual fork URL.

## Step LP.5. Read welcome status from `self.player`
Welcome screen currently hardcodes `Health: 20/20`, `Items: 0/8`. Read from `self.player.health`, `self.player.max_health`, `len(self.player.items)`, and `config.INVENTORY_LIMIT` (post-3.7).

---

# Out of scope for this plan

- Authentication for `server.py` (separate design doc; mentioned as future work in Step 1.4).
- Adding multiplayer or persistence beyond local saves.
- Switching the frontend off xterm.js to a structured-state UI (Step 4.2 only adds a sidecar query channel; full migration is a separate plan).

---

# Verification status (this plan)

- **Source:** `/review-senior` output, generated 2026-04-19, captured in this conversation.
- **What is verified by the review:** code references (file paths and line numbers in `computerquest/`, `server.py`, `tests/`), the existence of `data/*.json`, the missing `[project]` table, the `s` hotkey collision.
- **What is NOT verified yet:** that each fix lands cleanly without ripple effects (per-step verification covers this); that `archive/saveload.py` is actually portable to current code (Step 1.2 implement path requires inspection); that no other consumer reads `data/*.json` outside `computerquest/` (Step 3.2 includes a grep gate).
- **Verification method going forward:** per-step tests (unit, integration where relevant), and manual browser/CLI checks where the change is user-visible. The CI workflow (Step 2.3) backstops every merge.
