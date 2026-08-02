# Project State: Python-Zork

Phase: 3.3 Promote (complete) — no unit in flight
Approved: 2026-07-04T00:00:00Z by Michael (sha256:cde83dbaa90b; prose-style amendment 2026-07-06 sha256:8abdc57a3d45; decision 7 adaptive difficulty 2026-07-31 sha256:2949c0833fdf; fidelity-statement reconciliation + decisions 8 and 9 2026-08-01 sha256:3a650b2e76b6; decision 10 policy-knob simulators 2026-08-02 sha256:f9d9a851b941)

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

- 2026-07-04T00:00:00Z · sha256:cde83dbaa90b · docs/architecture-microquiz.md approved by Michael. Amended 2026-07-06 (prose-style pass, semantics unchanged; new sha256:8abdc57a3d45). Predict-and-verify micro-puzzle system: data model, simulator protocol with per-module fidelity statements, five new verbs, difficulty-weighted knowledge meter (cap 5), tiered hints, first-visit auto-prompt, save schema 1.1, eight-step migration plan. Deviations require /prd-amend and re-approval. Amended 2026-07-31: decision 7 adds adaptive difficulty (presentation-order only), approved by Michael; new sha256:2949c0833fdf.

_(Decision history predating the schema lives in `decisions.md` and project memory.)_

## Current Plan

**Micro-puzzle system (Direction C, predict-and-verify).** Full blueprint in `docs/architecture-microquiz.md` (decisions resolved 2026-06-26); deep-end minigame design in `docs/design-minigames.md`; research grounding in `mrf-knowledge/game-design/2026-06-22_teaching-games-text-adventure-pivot.md`.

Migration order (each step lands green): **1 simulators ✓ (4a50df1)** → **2 puzzle infra ✓ (4740077)** → **3 player/world wiring ✓ (a816658)** → **4 command surface ✓ (14cddbe)** → **5 content fill ✓ (28/28 puzzles, a510921)** → **6 knowledge-meter cutover ✓ (2252eee)** → **7 minigames consume simulators ✓ (756d910)** → **8 frontend per-room puzzle state ✓ (e08af0f, promoted)**. Microquiz unit COMPLETE.

Step 2 note: puzzles are one-YAML-per-file under `mechanics/puzzles/data/<category>/`, deserialized to frozen `MicroPuzzle` dataclasses, load-time-validated (the registry runs every setup through its named simulator, so a broken puzzle cannot ship). `registry.evaluate(id, raw)` is the single call step 4's commands will use. Three seed puzzles live (two cache, one pipeline). pyyaml is now a runtime dep per contract.

Step 1 note: cache (LRU/FIFO, direct-mapped→fully-associative) and pipeline (stall/forward RAW model) simulators landed with fidelity docstrings; timing conventions (write-through regfile, EX→EX forward, load-use bubble) documented in pipeline.py and pinned by tests (7/8/11 cycle counts). tlb/packet/storage/signature simulators land with their consuming puzzles in step 5.

`tk-a7098e` (4.1 minigames) is DONE: it was steps 1–7 above, all shipped and promoted. Step 4.2's browser verification is DONE (2026-07-03, headless Chromium walkthrough): welcome renders in xterm, typed command flows through the keystroke buffer into Game.feed, terminal prints the move, map re-renders live (Turn 1, current node CPU Package → Core 1). Three defects found and fixed during the walkthrough (d1b51e1). Full-victory playthrough re-verified live (34 turns, all 5 viruses, Victory:true) and the Railway deploy confirmed serving the current bundle.

**Save/load status (not a contradiction):** the Step 1.2 decision (2026-05-02) removed the *placeholder* save/load that silently lost data (99be8ed) and filed a follow-up to reimplement it properly. That follow-up (tk-24fa9f) shipped a real implementation (510ae26). The currently-wired `SaveLoadSystem` plus save/load/deletesave commands are the intended end state. The design docs' "in-flight puzzle/minigame state is not persisted" note is a scoping choice for that feature, not a conflict.

**Former "Out of scope" list, current status:** adaptive difficulty DONE (decision 7); in-flight puzzle persistence DONE (decision 8, minigame state still out); network/security simulators DONE on the policy-knob axis (decision 10, protocol fidelity and TCP still rejected); author-extensible puzzles CLOSED (Michael, 2026-08-02: no player-authored content).

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

**Live 28-puzzle playthrough (2026-07-28).** Browser-automated run against
production solving every shipped puzzle: 43 turns, 22 rooms, **28/28 solved,
0 failed**, all five knowledge areas at 5/5 (100%, 25/25). Verified against the
server snapshot (`solved 28 / available 28`) and the map header
(`28/28 puzzles`, 22 nodes marked solved, 0 partial). Plan was validated
locally first, then replayed live; results matched exactly.

Found and fixed one UI defect (a17353e): React Flow's MiniMap rendered 200x150
inside a 298x209 panel, covering ~48% of the map in opaque white on a dark UI
and hiding the graph it was meant to help navigate. fitView already frames the
whole ring at that size, so it showed an already-visible graph. Removed; the
zoom/fit Controls remain.

**Live combined playthrough (2026-07-29).** One browser-automated run doing
both: **28/28 puzzles solved AND all 5 viruses quarantined**, ending in
MISSION SUCCESSFUL with `game_ended {victory:true}`. 59 turns, 27/35 rooms.
Final stats read `Knowledge gained: 25` (the puzzle-free victory run reported
0), and the snapshot confirmed solved 28/28, quarantined 5, victory true,
knowledge 5/5 in every area.

Route deliberately defers the last virus (kernel's rootkit) so victory lands
after every puzzle is solved; all five virus rooms also hold puzzles, so one
route covers both goals. Plan was dry-run locally first and the live run
matched it exactly (same 59 turns, 27 visited, same totals).

This run reached achievements no earlier run could: the five per-area
knowledge experts plus **Computer Scientist** (max knowledge in all areas),
12 unlocked, score 2825. That exercises ProgressSystem's knowledge-gated
conditions, confirming puzzle-derived knowledge still drives achievements
after the Phase C single-writer change. No new defects found.

**Coverage pass (2026-07-29).** Verified all 35 rooms are reachable (max 4
hops), so no dead content and the visit-everything achievement is attainable.
Then closed the three worthwhile coverage gaps, project total 87% -> 91%,
tests 328 -> 373:

- `visualizer.py` 58% -> 100%. The `visualize`/`viz` command is advertised in
  help but half its render code had no test. Every alias and diagram now
  asserts on substance (stack layers, hierarchy levels, HDD vs SSD).
- `player.py` 77% -> 91%. The inventory branch of `quarantine` was dark
  despite being half the body collapsed during the DRY pass; also advscan
  gating and hidden-threat reporting, and the analyze hint ladder.
- `game.py` 72% -> 76%. The simulate cross-capability refusals (pattern/cache
  at the CPU sim, forward at the memory sim) were entirely untested.

Every new test was mutation-checked. The remaining `game.py` gap is
`setup_readline` and the CLI `input()` loop, deliberately skipped: terminal-only
plumbing whose mocking cost exceeds its value.

**Adaptive difficulty shipped (2026-07-31).** Contract decision 7, amending an
item that was explicitly out of scope. A room offering more than one puzzle now
orders its offer by the player's standing in that subject area: struggling
players meet the easiest first, strong players the hardest, everyone else keeps
the authored order.

Standing comes from signals already tracked, so no new persisted state: solved
puzzles, and puzzles attempted but still unsolved. `struggling` when unsolved
attempts at least match solves, `strong` after two clean solves with none
outstanding, `neutral` otherwise.

Scope was kept deliberately narrow. The gate (decision 2) still decides what is
visible at all, and the knowledge formula (decision 5) is untouched, so the
feature cannot unlock or award anything; a misjudged standing only changes which
puzzle leads. Adaptation is silent, and sorting is stable so equal-difficulty
puzzles never move. It bites in the six multi-puzzle rooms.

Verified: 14 new tests, mutation-checked in both directions (disabling
adaptation and flipping it fail the suite), and the full 28-puzzle + victory
playthrough is byte-identical at 59 turns. Confirmed live in production both
ways: a strong player is offered BIOS difficulty 3 ahead of difficulty 1, a
struggling player the reverse.

**Deploy note (2026-07-31).** Railway was degraded for roughly an hour: API
timeouts, JSON decode errors, a spurious "Unauthorized", and build logs that
would not stream. Two deploys hung in INITIALIZING/BUILDING while
`railway status` reported "Online", which only means the service is up on the
last *successful* build. Do not treat that as deploy confirmation. What settled
it was `railway deployment list`, which showed the real per-deploy state, plus
a functional probe of the live site. Keep using a behavioural probe rather than
status or a zero exit code to decide whether a deploy actually landed.

**Deploy verification (2026-07-31).** `/api/health` now reports the commit the
process is serving, and `scripts/deploy.py` refuses to call a deploy done until
the live endpoint returns the commit that was uploaded. Run it instead of bare
`railway up`; `--verify-only` answers "is production serving HEAD?" and exits
non-zero when it is not.

The commit comes from `DEPLOY_SHA`, set on the service with `--skip-deploys`
before uploading, falling back to `RAILWAY_GIT_COMMIT_SHA`. A file-based stamp
was tried first and cannot work: the uploader honours `.gitignore`, so an
ignored stamp never reaches the image. Dogfooding caught that, with the verifier
correctly refusing to pass a deploy reporting `commit: unknown`.

A commit stamp was chosen over a behavioural probe because it verifies any
change rather than one feature, so it never needs rewriting per deploy. The
build watch is only a progress display; the commit match is what decides.

**Prose check on the contract doc: no fix warranted (2026-07-31).** The AI-isms
script labels `architecture-microquiz.md` CRITICAL, but the doc scores
em/1k = 0.0 with no em-dashes and no emphasis-italics, and the rubric reserves
CRITICAL for >8/1k plus three other categories. All 8 hits across 4,744 words
were checked individually: the "let's" is the verb "Lets", the two hype verbs
are "unlock" in its literal game sense, and the five antithesis hits are real
technical contrasts ("data, not code"; "declarative, not derived"; "the gate is
on the listing UI, not on the engine"). Rewriting them would blur precise
statements and churn the sealed contract's sha for nothing. Left as is.

**Phase 0 hardening shipped (2026-08-01, PRD 1).** Three defects closed before
any feature work:

- **Shipped puzzle answers are now pinned.** The canonical answer is recomputed
  from simulator code and stored nowhere, so a simulator edit rewrote shipped
  content silently. Proven by mutating the signature scanner: it flipped
  `signature_first_match` to contradict its own printed explanation and all 404
  tests still passed. All 28 answers now assert against literals.
- **Simulator inputs are bounded.** The registry validates by *running* the
  author's setup, so unbounded values were executed at load. `size_lines: 10**9`
  allocated to OOM in about five seconds and SSTF's quadratic loop hung with no
  memory signature; both now raise instantly with a naming message. Bounds sit
  three to four orders of magnitude above anything shipped content uses.
- **The validator no longer swallows `MemoryError`** (it produced an empty
  "setup is not runnable: " and defeated watchdogs), and now cross-checks
  `answer_kind` against the simulator's, a mismatch that previously loaded
  cleanly and made every answer wrong forever.

Also reconciled the contract's per-simulator fidelity statements, which were
drafted before the simulators existed and had drifted in four places. No
simulator behaviour changed.

**Feature A shipped: in-flight puzzle state persists (2026-08-01, decision 8).**
Save schema 1.1 to 1.2. A save records the active puzzle's id, hints spent, and
prompted rooms; 1.0 and 1.1 saves still load with an empty session.

`prompted_rooms` is the field that actually fixes "the room re-offers its
puzzle": restoring the active puzzle alone does not, because auto-prompt only
bails while a puzzle is active and resumes the moment one is answered or
skipped. Persisting `hints_used` also closed an existing inconsistency, where a
reload kept the durable "attempted" mark but lost the counter, granting two more
free hints on the same puzzle.

Restore is deliberately tolerant, following the loader's existing treatment of
unknown component ids: an unresolvable puzzle id clears the puzzle and zeroes
the hints, a shortened hint list clamps the counter, unknown rooms are inert.
Only the id is stored, never the puzzle body, so a stale save cannot resurrect
deleted content.

**Feature B shipped: the false-positive security puzzle (2026-08-01).** One
YAML file, no code, bound to the kernel beside the one-byte-mutation puzzle it
references. The scanner is asked to scan its own quarantine log, which quotes
the signature it is reporting on, so it reports boot_sector_virus on a
completely harmless file.

This closes the pair the security content was missing. `signature_near_miss`
shows a scanner missing a real virus; this shows one accusing an innocent file.
Neither is a matching bug; both follow from what pattern matching can know. The
intuitive answer ("clean") is graded wrong, which is the point.

Puzzle count 28 to 29. Two tests were coupled to the literal 28 and now assert
behaviour instead: the bounds test checks that content validates at all, and the
e2e checks the badge ticks 0 to 1 without pinning a total the golden fixture
already owns.

**PRD 2 shipped: difficulty modes (2026-08-01, decision 9).** `difficulty
<mode>` (alias `mode`) selects what a hint costs. `standard` is decision 3
unchanged and remains the default. `learning` makes hints free and never marks a
puzzle attempted. `strict` withholds hints while leaving the post-answer
explanation intact, so a strict player still learns from a wrong answer.

Save schema 1.2 to 1.3 for the preference; 1.0 through 1.2 saves restore
`standard`, and an unrecognised mode in a file falls back rather than refusing
the save. Decision 5 holds in every mode: the modes change only whether a hint
records an attempt, never the knowledge formula, and a test asserts that for all
three.

The schema bump PRD 2 hoped to share with Feature A was no longer available,
since A had already shipped at 1.2. Both bumps are additive and tolerant.

**PRD 5 shipped: help auto-pagination (2026-08-01).** The client reports its
xterm height on start and on resize; the server pages long output to it and
holds the rest behind `--more--`, which Enter advances without running a
command. No reported height means everything is emitted whole, as before.

Scope was corrected during implementation. The first version paged *every*
command's output, which split room descriptions across pages and failed all
three end-to-end tests. That was a real design error, not a test problem: paging
narrative output ruins the flow of play. Pagination now applies only to
reference output the player explicitly asked for (help, map, motherboard,
achievements, stats, knowledge). A test pins that narrative output never pages.

No contract amendment: this is presentation, and the content functions still
return whole strings, so the byte-exact golden fixtures stay valid.

**PRD 3 shipped: objectives (2026-08-01).** `objectives` (alias `next`) answers
"what should I do now", showing at most four items derived entirely from live
state: pending quarantines, a puzzle in this room, unexplored regions, and the
thinnest knowledge area. Read-only, consumes no turn, and does not disturb an
active puzzle.

It deliberately does not spoil the search. Unlocated viruses are pointed at by
*region* ("the PCIe complex"), never by room, because finding one is the
investigation that `scan` exists for. Once a virus is found, naming its room
becomes help rather than a spoiler, and a test pins both halves.

Two defects were caught by looking at the rendered output rather than trusting
green tests: the panel used a fixed-width box that could not align around
variable-length text, and it reported "5 of 5 viruses still loose" while
simultaneously telling the player to quarantine one they had just found. The
panel now uses rules with wrapping, and the count reports viruses still
*unlocated*. Both are pinned.

**PRD 4 shipped: web tab completion and per-command help (2026-08-01).** Tab in
the browser now completes commands, directions, room items, inventory items,
puzzle ids, about-topics and virus names. Candidates are generated server-side
by `Game.completions()`, so the browser holds no copy of the command table or a
room's contents and cannot drift from either. The CLI readline completer and the
socket both call the same method.

Argument pools stay per-verb, preserving the special case the readline completer
already had: `take` offers only room items, `drop` only inventory, `solve` only
puzzles bound to this room.

`help <command>` returns one entry instead of all 70+ lines, reading its
descriptions out of the full help screen rather than introducing a second table
that could drift from it. An unrecognised topic falls back through prefix, then
substring, then difflib, so `help scn` finds `scan`.

Tab never reaches the game: the client intercepts it and asks for completions,
so the input caps and the line buffer are untouched.

Two rendering defects were found by driving real Tab keystrokes in the deployed
browser, neither visible to any test. Completing a single match first inserted
the whole match on top of the prefix already typed, then, once that was fixed to
insert only the remainder, rendered it twice because the client wrote locally
*and* the server echoed the input back. Ordinary typing has always relied on the
server echo alone. Both fixed; `sol` + Tab now yields exactly `solve`.

The first of those was masked in play: the dispatcher's difflib fallback
resolved `solveve` to `solve`, so the game behaved correctly while the line read
wrong. Only looking at the screen caught it.

**Full live playthrough (2026-08-02).** One browser run exercising everything
shipped this session: **29/29 puzzles solved and all 5 viruses quarantined**,
MISSION SUCCESSFUL at 59 turns, 27/35 rooms, knowledge 25/25. Snapshot confirmed
solved 29/29, victory true, and the map header read `29/29 puzzles` with 22
solved nodes and no minimap. Matched the local dry run exactly.

Also exercised in the same run: `objectives` at the start and again near the end
(where it correctly narrowed to "1 of 5 viruses are still unlocated"),
`difficulty` reporting and setting a mode, `help quarantine` returning a single
entry, and a save/load round trip mid-run that preserved knowledge at 25/25.

Found one defect. Pagination matched on verb *strings*, so `map` paged while its
documented shortcut `m` did not: a one-character verb never resolves through the
prefix matcher, and `m` was not in the literal set. Same for `h` and `mb`.
Paging is now decided by the command *class* from the registry, which covers
every alias by construction.

The probe nearly hid it. Testing `m` straight after `map` appeared to pass,
because sending `m` was advancing the pager left pending by `map` rather than
paginating on its own.

**Targeted review of the new surface (2026-08-02).** The last full review was
2026-07-26; 1,773 insertions had landed since across code that had never been
reviewed (objectives.py, the pagination and completion paths, HintMode,
content/, scripts/deploy.py). Four reviewers swept it; every finding below was
independently reproduced before being acted on, after the YAML retraction
earlier the same day.

Eight defects fixed in ba6b181, all verified live afterwards:

1. `objectives` declared victory with a virus in the player's pack. Viruses are
   ordinary items and `take` accepts them without a scan, so the pack was a
   hiding place the room sweep never checked.
2. The pager swallowed a command typed at `--more--`, discarding the line.
3. Ctrl-C drew a fresh prompt while leaving the pager armed, so the UI lied
   about its own state.
4. `maybe_auto_prompt` bypassed the difficulty gate, presenting puzzles `solve`
   refuses to show and letting a fresh player bank knowledge from nothing.
5. Difficulty modes inverted adaptive ordering: `area_standing` read
   `attempted_puzzles`, which learning mode stops writing, so a struggling
   beginner was classified strong and served the hardest puzzle first.
6. `solve`/`hint`/`skip`/`difficulty` were declared read-only while writing
   state schemas 1.2 and 1.3 persist, so quitting after them lost the work.
7. Tab completion offered puzzle ids the gate hides; since `solve <id>`
   deliberately bypasses the gate, one keypress defeated progression.
8. Arrow keys typed `[A` into the command line. `[` is itself inside the `@`-`~`
   terminator range, so a naive check ended the sequence a byte early.

Three of these were in code written earlier the same session, and two were
self-inflicted (adding `difficulty` to the read-only set, and building
completion from the raw room list rather than the gated one).

Six existing tests were updated because they pinned the old buggy behaviour.

Gating the auto-prompt initially silenced Core 1, the first room north of the
start, because its puzzle was difficulty 2. Rather than weaken the gate,
`pipeline_forwarding_intro` was retuned to difficulty 1 (Michael's call). That
is the better reading of the content anyway: it is literally the intro, its pair
is "the same chain with forwarding off", and counting cycles *with* forwarding
is the easier of the two. It also creates a real ramp, since solving it now
unlocks its own difficulty-2 pair. cpu keeps 10.0 total weight against a cap of
5, and a full playthrough still maxes every meter.

**Deferred findings closed (0eb4d75, 2026-08-02).** Six findings had been held
back from ba6b181 pending independent reproduction. All six were reproduced by
running the code, then fixed:

1. `commit_matches` compared on the shorter of the two SHA widths, so a
   one-character stamp matched almost any HEAD and reported a green deploy.
   Now floored at seven, git's own short-sha width.
2. `parse_deployments` accepted any pipe-separated row whose first column had
   no spaces, so a column header parsed as a deployment id the watcher would
   poll until the build timeout. Now requires a UUID.
3. `_run` raised `FileNotFoundError` when the `railway` binary was absent.
4. The client's line mirror diverged from the server's buffer three ways:
   Ctrl-C never cleared it (so Tab completed against text the server had
   discarded), a pasted chunk was appended whole rather than walked per
   character, and two copies of the mirror were written in different places.
   The mirror moved to `src/completion.ts`, where it is tested against
   server.py's rules instead of against a copy of them.
5. `save_load._apply` read and wrote in one pass, so a save valid down to its
   last key left the player moved and re-inventoried by the half that had
   already run. It now validates everything before writing anything, and no
   longer reads `knowledge` from the file at all, that being derived state.
6. `recompute_knowledge` seeded its tally from the dict it was replacing, so a
   hand-edited save could add areas that survived, and one missing an area
   raised `KeyError` on the first puzzle scored into it.

Plus one found while verifying: flask-socketio runs with `async_handlers` on,
so every event is dispatched in its own thread and two keystrokes from one
client raced on the line buffer, the later write dropping the other's
characters. Input is now serialized per session. The regression test was
initially vacuous (it passed against a deliberately unserialized mutant); the
delay had to be moved into the echo, which is the only point between the
buffer read and the buffer write.

Two reviewer claims did not survive checking and were dropped: `difficulty` is
not ambiguous with any prefix (`d` is the deliberate alias for `down`, `di`
resolves cleanly), and the `_apply` rollback concern was real but narrower
than described.

Verified live on production afterwards: Ctrl-C then Tab now lists all commands
instead of inserting `ve` onto an empty line; a `look\rkno` paste runs `look`
and leaves `kno` for Tab to complete to `knowledge`; and a solve/save/move/load
roundtrip restores both the knowledge meter (1/25) and the room.

**Feature B completed (2026-08-02).** PRD 1's decision 3 sequenced items 2 to 4
as step 4 of a five-step build order; a later summary called that "deferred",
which misread it. Built as contract decision 10 (new sha256:f9d9a851b941).

The reasoning is the policy knob, not protocol depth. `packet` and `signature`
are accurate but have no setting whose flip changes the answer on a
byte-identical setup, which every other simulator does have, so puzzles over
them can only ask the player to read the setup back. Three new modules, with
`packet.py` and `signature.py` untouched so their nine puzzles keep their
answers:

- `scan_all` reports one verdict per database entry instead of stopping at the
  first hit. Puzzle `scan_report_all_matches` (bios) reuses
  `signature_first_match`'s bytes exactly.
- `scan_wildcard` carries an exact/wildcard knob. Puzzle
  `scan_wildcard_mutation` (usb_ports) reuses `signature_near_miss`'s file, so
  the same bytes that were clean under exact matching are a hit under a
  widened pattern.
- `link_cost` carries a store-and-forward/cut-through knob. Puzzles
  `link_store_and_forward` and `link_cut_through` (ethernet) are the same pair
  device as `hdd_seek_fcfs`/`hdd_seek_sstf`: identical setup, one key changed,
  36 ticks against 16.

Puzzle count 29 to 33. Every subject area now holds 7 puzzles except storage
(5), and all five still saturate on a full solve. Both touched areas were
already past the cap (networking 7.5, security 6.0), so this is content value
rather than progression value, as flagged before authoring.

`scan_all`'s report shape was redesigned mid-build after playing it: returning
only the matches made the answer's length part of the answer, and a length
mismatch is treated as a wrong shape (ungraded, free retry), which told the
player their count was off. One slot per database entry fixes it.

**Player-authored puzzles are closed (Michael, 2026-08-02).** PRD 1's Feature C
open question is settled in favour of more in-repo puzzles. No user-directory
loading, no id namespacing, no `room:` key, no `source` field. Still open and
unrelated to who authors: `answer_kind` is never checked against the
simulator's own `answer_kind`, so a mismatch loads cleanly and makes every
answer wrong forever.

## Branch & Tests

- Branch: `staging`
- Working tree: clean
- Last CI: green (Python matrix + frontend + e2e) @ 0eb4d75 (Feature B commit pending)
- `staging` and `main` are in sync at 0eb4d75 (all refs, local and origin).
- Production verified serving 0eb4d75 via `/api/health`.
- Tests: 577/577 via `uv run pytest` (coverage 91%); 33 puzzles; ruff clean; mypy clean (required in CI, Python 3.11+3.12 matrix). Frontend: 34 vitest + 3 Playwright e2e green.
- npm audit: 0 vulnerabilities (was 20).
- Canonical test fixture: `tests/_helpers.py::build_real_game`
- Known, out of gate: `scripts/deploy.py` has one pre-existing mypy
  `no-any-return` on `fetch_health`. CI checks `computerquest` only.

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
- 2026-07-28T00:00:00Z live 28/28 puzzle playthrough; removed the map minimap covering half the panel (a17353e); promoted and redeployed
- 2026-07-29T00:00:00Z live combined playthrough: 28/28 puzzles + 5/5 viruses + victory, knowledge 25/25, 12 achievements; no defects found
- 2026-07-29T00:00:00Z coverage pass: visualizer/player/simulate surfaces tested, 87% -> 91%, 373 tests (934c872, 2dc840b, e0cb224)
- 2026-07-31T00:00:00Z 1.2 -> 1.3 contract amended: decision 7 adaptive difficulty approved by Michael (sha256:2949c0833fdf)
- 2026-07-31T00:00:00Z 2.1 -> 2.3 adaptive difficulty implemented and verified; 387 tests
- 2026-07-31T00:00:00Z deploy verification added (cc6d54f, 642ffc6); prose check on the contract doc reviewed and dismissed as false positives; 404 tests
- 2026-08-01T00:00:00Z PRD backlog added and PRD 1 approved/scoped; Phase 0 hardening shipped; 425 tests
- 2026-07-26T00:00:00Z code-review remediation shipped: bugs B1-B8, dead-code removal, DRY, deploy hardening (a43897d..efede42); 297 tests; promoted to main
- 2026-08-02T00:00:00Z 2.3 deferred review findings closed (0eb4d75): deploy hardening, client line mirror extracted and tested, save loader validates before writing, per-session input lock; 547 tests; promoted and deployed
- 2026-08-02T00:00:00Z 1.3 -> 2.3 contract decision 10 (policy-knob simulators, sha256:f9d9a851b941); Feature B items 2-4 built: scan_all, scan_wildcard, link_cost + 4 puzzles; 33 puzzles, 577 tests
