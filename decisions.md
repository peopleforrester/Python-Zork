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

## 2026-07-04T00:00:00Z · 1.3 · microquiz architecture approved

Michael approved docs/architecture-microquiz.md as the contract for
the predict-and-verify micro-puzzle unit (tk-a7098e).
sha256:cde83dbaa90b18bdec1c05ffadb18f1d603f70ee0dc8e9b536820610c6bc8555.
Alternatives (stay-the-course portfolio piece; full Zachtronics-style
pivot) were rejected in the 2026-06-22 research spike. Implementation
follows the doc's eight-step migration plan, TDD-first per step.

## 2026-07-06T00:00:00Z · amendment · prose-style pass over the contract doc

Michael directed an AI-isms sweep over all repo prose. The sealed
contract (docs/architecture-microquiz.md) had 38 em-dashes plus a few
splices; all replaced per the prose-style rule. No decision, schema,
verb, or plan-step content changed. New sha256:8abdc57a3d45. Same pass
cleaned README (also fixing stale PTY-era architecture and security
text), PROJECT_STATE, plan.md, design-minigames.md, and the three
puzzle YAML files.

## 2026-07-25T00:00:00Z · reconciliation · state files corrected to actual shipped state

PROJECT_STATE.md and tasks.yaml had drifted: they still declared Phase 2.1
Test, 150 tests, and CI at d1b51e1, while the repo had shipped the full
eight-step microquiz unit plus a frontend test-suite unit and an npm-audit
cleanup, all promoted to main (all refs at 6349499, 277 pytest + 14 vitest +
3 Playwright e2e green). Marked tk-a7098e done, advanced the lifecycle
checklist to 3.3 complete, updated Branch & Tests, and appended phase-history
lines. No code changed. Recorded the open save/load contradiction (code keeps
save/load; an earlier decision said remove it) as still needing a call from
Michael.

## 2026-07-25T00:00:00Z · correction · save/load is not an open contradiction

Corrects the prior entry, which called the wired save/load an "open
contradiction." It is not. The Step 1.2 decision (2026-05-02) removed only the
placeholder save/load that silently lost data (99be8ed) and filed a follow-up
to port a real one from archive/saveload.py. That follow-up (tk-24fa9f) shipped
the real implementation (510ae26). The current SaveLoadSystem plus
save/load/deletesave commands are the intended end state. No decision from
Michael is pending on this.

## 2026-07-26T00:00:00Z · review · code-review remediation scope approved and shipped

A five-lens review (architecture, Python correctness, mechanics, frontend/server,
refactor) surfaced eight bugs plus cleanup and hardening opportunities. Michael
chose scope "Bugs + cleanup" (Phases 1-3) plus deploy/security hardening (Phase
4), and explicitly DEFERRED the larger structural work (game.py god-object split,
knowledge single-writer, visited/id-space dedup) as not-a-live-bug. Shipped in
four commits a43897d..efede42, staging CI green, ff-merged to main. Test count
277 to 297. The deferred structural items are recorded in PROJECT_STATE for a
future decision.

## 2026-07-27T00:00:00Z · refactor · deferred structural work completed

Michael asked for the structural items the earlier review had deferred. All
four shipped: static-content extraction out of game.py (guarded by a
byte-exact golden fixture), PuzzleSession extraction, knowledge reduced to a
single writer, and the visited/id-space duplication removed.

The visited work turned out to fix a live defect rather than a latent one: at
turn 0 the starting room was recorded visited in map_grid but not on the
Component, so the ASCII map and the React map disagreed, and the web map
reported 0/35 visited while the player stood in a room. map_grid is now
derived from Component.visited.

Knowledge rewards were removed rather than made durable, because the approved
contract (architecture-microquiz.md, Knowledge meter) defines knowledge as a
function of demonstrated solves; granting it from an achievement would be a
contract deviation requiring re-approval, not a bug fix.

game.py 1114 -> 772 lines, tests 297 -> 318. CI green, promoted to main,
redeployed to Railway and verified live in a browser.

## 2026-07-31T00:00:00Z · 1.3 · amendment · decision 7, adaptive difficulty

Michael asked for the adaptive-difficulty feature, which the sealed contract
listed under "Out of scope" ("the puzzle order is room-determined, not
player-skill-determined; a future pass could re-order based on solve history").
Implementing it therefore required amending the contract, not just coding.

Two design forks were put to Michael before any source was touched. He chose
(a) reorder within a room in both directions, leaving the gate and the
knowledge formula alone, over the wider options of relaxing the unlock gate for
strong players or adding scaffolding for strugglers; and (b) silent adaptation
over announcing it, so a struggling player is not told the game thinks they are
struggling.

The narrow scope is the point: because the feature only reorders, it cannot
open a gate or grant knowledge, so a wrong standing costs a player nothing but
which puzzle appears first. Standing reuses signals already tracked, so no new
save state and no schema bump.

Contract body updated (decision 7 added, the out-of-scope bullet struck);
new sha256:2949c0833fdf.

## 2026-08-01T00:00:00Z · 2.2 · Phase 0 hardening (PRD 1)

Michael approved PRD 1 with Feature C parked, Feature A scoped to puzzle state
only, Feature B scoped to the one zero-code puzzle, and Phase 0 first.

Phase 0 closed two defects found during research and one documentation drift.

Shipped puzzle answers were unguarded: the canonical answer is recomputed from
simulator code on every call and stored nowhere, so a simulator edit rewrote
shipped content silently. Demonstrated by mutating the signature scanner to take
the last match instead of the first, which flipped signature_first_match's answer
to contradict its own printed explanation while all 404 tests passed. All 28
answers are now pinned to literals.

Author-supplied setup values were unbounded, and the registry validates a puzzle
by running it. A single integer made the cache simulator allocate to OOM in
about five seconds, and SSTF is quadratic so a long request list hung with no
memory signature. Both now raise immediately with a naming message. The bounds
sit three to four orders of magnitude above anything shipped content uses.

The validator also relabelled MemoryError as an empty "setup is not runnable: "
and swallowed watchdog signals; those now propagate. A missing answer_kind
cross-check was added at the same seam, since a mismatch previously loaded
cleanly and then made every answer wrong forever with no error.

The contract's per-simulator fidelity statements were drafted before the
simulators existed and had drifted: they promised ARP and link-layer framing
never implemented, structural hazards not modelled, and an SSD remap counter
that does not exist, while omitting the first-match rule signature_first_match
depends on. Reconciled to the module docstrings verbatim. No simulator behaviour
changed; new sha256:65767d1a411e.

## 2026-08-01T00:00:00Z · 1.3 · amendment · decision 8, in-flight puzzle persistence

Approved as part of PRD 1, scoped by Michael to puzzle state only. Minigame
state stays out of scope, so `design-minigames.md` is untouched and its
"do not re-litigate" note stands.

A save now records the active puzzle's id, hints spent, and the rooms that have
already auto-prompted. The body is never serialized; only the id, so a stale
save cannot resurrect deleted or rewritten content. Restore tolerates drift the
way the loader already tolerates unknown component ids: an unresolvable id
clears the puzzle and zeroes the hint count, a shortened hint list clamps the
counter, unknown prompted rooms are inert.

The original exclusion justified itself only by mirroring the minigame decision,
whose rationale was that active sessions are not long-running state worth
persisting. That reasoning survives for minigames and does not for puzzles:
`prompted_rooms` is what stops a room re-offering a puzzle the player set aside,
and losing the hint counter while keeping its durable consequence meant a
reloaded game handed out two more free hints on an already-attempted puzzle.

Schema 1.1 to 1.2; 1.0 and 1.1 saves still load with an empty session. Knowledge
untouched. New contract sha256:73cd234c9b75.

Prose note: the antithesis count in the contract rose by one during Phase 0's
fidelity reconciliation, from quoting tlb.py's docstring verbatim ("an unmapped
VPN is an authoring error, not a simulated fault"). Rewording it would restore
the doc/code drift that reconciliation removed, so it stays.

## 2026-08-01T00:00:00Z · 1.3 · amendment · decision 9, difficulty modes

PRD 2. Decision 3 fixed one hint bargain for every player: first free, second
marks the puzzle attempted. That is now `standard` and is unchanged.

`learning` waives the attempt mark so a new player can lean on hints without
quietly forfeiting the knowledge they are about to earn. `strict` withholds
hints for a harder replay but deliberately leaves the post-answer explanation
running, since the explanation is where the teaching lives and removing it would
make strict mode punitive rather than harder.

Knowledge was the thing to protect. Decision 5 makes it a pure function of
solved puzzles with PuzzleSession as the single writer, so the modes were built
to touch only whether a hint records an attempt. A test asserts the meter does
not move for any of the three modes.

Schema 1.2 to 1.3 for the preference. PRD 2 had asked to share a bump with
Feature A, which was no longer possible because A shipped first; both bumps are
additive and older saves restore `standard`. New sha256:3a650b2e76b6.

## 2026-08-02T00:00:00Z · correction · the YAML alias-bomb finding was wrong

PRD 1 recorded three DoS vectors for author-supplied puzzle content. Two were
reproduced independently before being written down: the cache `size_lines`
memory blowup and the quadratic SSTF loop, both closed in Phase 0.

The third, YAML alias expansion exhausting memory during `safe_load` before any
validation runs, does not reproduce. PyYAML resolves aliases to shared
references rather than copies, so a 508-byte bomb with 9^11 nominal elements
loads in 0.00s and allocates almost nothing.

That claim came from the research subagent and went into the PRD and
PROJECT_STATE without the independent check the other two got. Retracted in both
places. The practical effect is that the security picture for author-extensible
puzzles is better than recorded: Phase 0 already closed the vectors that were
real, and there is no known pre-validation parser vector.

## 2026-08-02T00:00:00Z · review · targeted review of the post-2026-07-26 surface

Scoped to code added since the last full review rather than repeating it: the
core had been reviewed and its findings closed, while ~1,773 new lines had never
been looked at. Four reviewers, findings reproduced independently before action.

Eight defects fixed. The two most serious were a false "nothing left to do" from
`objectives` while the game was unwinnable, and a pager that silently ate typed
commands. Three came from work done earlier the same session and two of those
were self-inflicted.

Two design points settled while fixing:

Auto-prompt now honours decision 2's gate. This changes onboarding: Core 1, the
first room north of the start, no longer presents a puzzle because that puzzle is
difficulty 2. Checked that four difficulty-1 puzzles sit two hops from the start,
so a new player still meets the mechanic quickly. The alternative, letting the
auto path show what the command path refuses, is exactly the inconsistency that
allowed knowledge to be banked from a standing start.

Adaptive standing now reads a mode-independent struggle signal (helped or gave
up), recorded in every hint mode and persisted with the session, rather than
`attempted_puzzles`, which decision 3 writes only in STANDARD. Without the split
the two features silently coupled and the beginner mode was the one classified
"strong".

## 2026-08-02T16:20:00Z · 2.3 · Deferred review findings closed (0eb4d75)

Six findings held back from ba6b181 pending independent reproduction were each
reproduced by running the code, then fixed: three in `scripts/deploy.py` (a
SHA comparison with no minimum width, a deployment parser that accepted column
headers, an uncaught `FileNotFoundError`), the client's line mirror diverging
from the server buffer on Ctrl-C and on pasted chunks, a save loader that
mutated the game before it finished validating, and a knowledge tally seeded
from the dict it was replacing.

The mirror moved out of the App.tsx closure into `src/completion.ts`. The old
`completion.test.ts` defined and tested its own copy of the logic, so the
shipped path had no coverage at all and the Ctrl-C and paste defects lived in
the untested half.

Two claims from the review did not survive checking and were dropped rather
than "fixed": `difficulty` is not ambiguous with any prefix, since `d` is the
deliberate alias for `down` and `di` resolves cleanly; and the `_apply`
rollback concern was real but narrower than the reviewer described. This is the
same discipline adopted after the YAML alias-bomb retraction on 2026-08-01.

One new defect surfaced while verifying: flask-socketio runs with
`async_handlers` on, so each event is dispatched in its own thread and two
keystrokes from one client raced on the line buffer. Input is now serialized
per session with a per-sid lock, chosen over turning `async_handlers` off
because that would serialize every client against every other. Keystrokes from
one terminal are ordered by nature, so the lock costs nothing real.

The regression test for that race was vacuous on first writing: it passed
against a mutant that handed out a fresh lock per call. The injected delay sat
before the buffer read rather than between the read and the write, leaving the
window microseconds wide. Moving the delay into the echo, which is the only
call between them, made the mutant lose exactly the three characters described.
Worth recording as the general rule: a concurrency test that has not been run
against an unsynchronized build has not been shown to test anything.

## 2026-08-02T17:05:00Z · 1.3 · Contract amended: decision 10, policy-knob simulators

Michael corrected the record: Feature B's larger simulator work was never
deferred. PRD 1's decision 3 sequenced it as step 4 of a five-step build order,
and a later summary described that as "deferred by user", which misread a
sequencing call as a cut. Items 2 to 4 are now built.

Contract amended with decision 10 and two new fidelity statements; new
sha256:f9d9a851b941 recorded in PROJECT_STATE.md and in the ABOUTME headers of
`puzzles/types.py` and `puzzles/__init__.py`.

The reasoning the decision records: `packet` and `signature` are accurate but
knobless, and every other simulator has a setting whose flip changes the answer
on a byte-identical setup. Puzzles over a knobless simulator can only ask the
player to read the setup back, so the fix for "low-fidelity networking and
security" is a counterfactual rather than protocol depth. `scan_all`,
`scan_wildcard` and `link_cost` land as new modules; `packet.py` and
`signature.py` are untouched, so the nine puzzles built on their answers keep
them.

Four puzzles: `scan_report_all_matches` (bios) and `scan_wildcard_mutation`
(usb_ports) reuse byte-identical setups from `signature_first_match` and
`signature_near_miss`, so each is a literal counterfactual on the file the
player has already scanned. `link_store_and_forward` and `link_cut_through`
(ethernet) are the same pair device as `hdd_seek_fcfs`/`hdd_seek_sstf`:
identical setup, one key different.

## 2026-08-02T17:10:00Z · 2.2 · Multi-match report is per-entry, not a match list

Caught while playing the new content rather than by a test. The first design
had `scan_all` return just the matching names, which made the answer's *length*
part of the answer. `PuzzleSession.answer` treats a sequence length mismatch as
a wrong *shape*: ungraded, no attempt recorded, free retry. On every shipped
sequence puzzle that is right, because the count is fixed by the prompt. Here it
told a player who answered one name that their count was wrong, which on a
two-entry database is most of the answer.

Fixed by reporting one verdict per database entry, naming the signature where it
matched and `clean` where it did not. The length is now fixed by the database
the prompt displays, so a short answer is genuinely malformed and a wrong
verdict is genuinely wrong and graded per position.

`MAPPING` was the other candidate and was rejected: no shipped puzzle uses it,
and its grader compares with plain `==` while SEQUENCE and CHOICE both fold
case, so this puzzle would have been the first user of a path where a correct
answer in the wrong case is marked wrong.

## 2026-08-02T17:12:00Z · 1.3 · Player-authored puzzles closed

Michael: no more player-authored content. PRD 1's Feature C open question is
settled in favour of more in-repo puzzles. The user-directory layer is closed:
no `~/.computerquest/puzzles/` loading, no id namespacing, no `room:` key, no
`source` field.

This also retires the room-binding concern that was being raised as a blocker.
Binding is a literal list in `architecture.py::bind_puzzles`, and the YAML's
`component_category` is descriptive only, so a puzzle file with no entry in that
list is unreachable. That only ever mattered for content arriving from outside
the repo; for puzzles authored here, adding the file and one line to that list
is the whole job, and a test already asserts nothing is left unbound.

Not closed by the answer: the validation CLI is repo tooling, and the defect it
was going to catch is real. `answer_kind` is never checked against the
simulator's own `answer_kind`, so a mismatch loads cleanly and makes every
possible answer wrong forever, with no error at any layer. Worth closing
whoever writes the puzzles. Not in flight.

## 2026-08-02T20:15:00Z · 2.3 · Authoring validator built; a stale claim corrected

The `answer_kind`-versus-simulator check was reported as an open defect. It is
not: Phase 0 added it in `e5795bb` ("fix the validator") and it lives at
`registry.py:159`, raising `PuzzleDataError` that names both kinds. Verified by
loading a deliberately mismatched puzzle. The claim came from PRD 1's Feature C
section, written before that fix landed, and was repeated from the document
instead of checked against the code. Both PRD 1 and PROJECT_STATE now carry the
correction.

`scripts/validate_puzzles.py` built as the surviving piece of Feature C. It
reports every problem in one pass rather than dying on the first file, prints
each canonical answer, checks the header comment still states it, and names any
puzzle bound to no room.

The header check earns its place: every shipped file records its answer in a
comment, that record was the author's claim, and nothing verified it. All 33
were checked and all 33 are accurate. Two state theirs in hex (`0x1ABC` rather
than 6844), which a first naive comparison reported as drift, so the comparison
accepts both spellings and treats bool separately, since bool is an int
subclass and `hex(True)` is `0x1`.

Two defects in this work were found by mutation testing rather than by writing
it carefully:

The reachability assertion was vacuous. `check_tree` takes `check_binding` and
the test omitted it, so `unbound` was always empty and the assertion passed
against any tree. Removing a real binding did not fail it.

`_bound_puzzle_ids` then turned out to be wrong in the opposite direction:
`bind_puzzles()` runs inside `ComputerArchitecture.setup()`, not the
constructor, so constructing the object and reading `rooms` saw nothing and
every puzzle read as unbound. The vacuous assertion had been hiding it. With
both fixed, removing one binding names exactly that puzzle.

That is the second vacuous test in two days, after the concurrency one. Same
lesson, worth stating once: a guard that has not been run against a build it is
supposed to reject has not been shown to guard anything.

## 2026-08-02T20:45:00Z · 2.3 · Housekeeping sweep

Four findings from an audit that turned up no live defects. Recorded because
three of them are about test coverage rather than behaviour, and coverage gaps
are what the last several real bugs hid in.

`PuzzleRegistry.by_category` removed. It was built on every load and read
nowhere outside the registry: rooms bind puzzles by id in `architecture.py`,
and `component_category` is descriptive, so nothing ever looked a puzzle up by
it. The one test covering it asserted that the loader could count its own
output; replaced with one asserting every puzzle declares a known category.

All 79 registered verbs are now exercised. Six (`?`, `c`, `clear`, `cls`,
`next`, `r`) were reachable by players and appeared in no test at all. Each was
run by hand first and all six were correct, so this pins working behaviour
rather than fixing a bug. The sweep asserts no verb crashes bare or with a
nonsense argument, none answers "not recognized", and none returns nothing;
plus the inverse, that an unregistered verb still is rejected, so the three
cannot pass by the resolver becoming permissive. `quit`/`exit`/`q` are excluded
because they call `input()` in the CLI build.

`App.tsx` now has unit tests. Previously only the three Playwright specs drove
it. xterm and socket.io are mocked: jsdom has no layout so a real Terminal
cannot fit or render, and the subject is which bytes App forwards and when,
which is App's own logic. Mutation-checked against reverted Ctrl-C and paste
handling in `completion.ts`; both mutants fail at the App level, not only in
the module's own tests.

`fetch_health` in `scripts/deploy.py` returned `Any` from `json.loads`, which
mypy flagged and CI never saw because it checks `computerquest` only. It now
returns `{}` for a payload that parses to something other than an object, which
is what the caller already assumed when it read `commit` off the result.

Left open deliberately: 11 of 35 rooms hold no puzzle and storage has 5 against
7 in every other area. That is an authoring decision, not a defect, and the
question worth answering is whether `gpu` and `memory_controller` deserve
puzzles rather than whether every room needs one.
