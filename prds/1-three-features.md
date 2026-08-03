# PRD 1: Persistence, simulator fidelity, and author-extensible puzzles

Status: **approved 2026-08-01 by Michael, scoped as below**
Author: research pass 2026-08-01
Contract affected: `docs/architecture-microquiz.md`, `docs/design-minigames.md`

Three features were requested together. Research found they share two
prerequisites, and that both prerequisites are defect fixes worth doing whether
or not any feature ships. That reordering is the main recommendation here.

---

## The two findings that reorder the work

### F1. Shipped puzzle answers are completely unguarded

No test asserts the canonical answer of any shipped puzzle. `test_puzzle_data.py`
checks only that the answer's *type* matches its `answer_kind`.

Demonstrated: mutating `simulators/signature.py` to take the last match instead
of the first flips `signature_first_match` from `boot_sector_virus` to
`rootkit_virus`. That contradicts the puzzle's own printed explanation, which
tells the player the scanner walks its database in order. **All 404 tests
passed.** The only record of each expected answer is a `#` comment at the top of
each YAML file.

Consequence: any change to a simulator can silently invalidate shipped content
and leave its explanation prose factually wrong, with CI green. Feature B is
unshippable until this is closed, and Feature C makes it worse by inviting more
simulator inputs.

### F2. Author-controlled scalars cause unbounded memory and CPU

Reproduced independently:

| Vector | Input | Result |
|---|---|---|
| `cache.size_lines: 10**9` | 283-byte file | MemoryError after 5.1s; without an rlimit this is OOM |
| SSTF `requests` | n=2000 → 0.15s, n=8000 → 2.97s | quadratic; a 269 KB file does not finish |
| ~~YAML alias expansion~~ | ~~343-byte file~~ | **RETRACTED 2026-08-02: does not reproduce.** PyYAML aliases are shared references, not copies; a 508-byte bomb with 9^11 nominal elements loads in 0.00s. This came from the research agent and was recorded without independent verification, unlike S1 and S3 which were reproduced first. |

`registry._validate_playable` validates by **executing** `simulator.run(setup)`.
That is elegant for trusted content and dangerous for untrusted content. Its
blanket `except Exception` also relabels `MemoryError` as
`"setup is not runnable: "` with an empty message, and swallows signal-based
watchdogs, which blocks the obvious mitigation.

This is a **local footgun today** (a user directory is written by the user who
runs the game) but note `server.py` constructs a fresh `Game()` per socket
connection, and `Game.__init__` calls `load_registry()` unguarded. If user
content is ever loaded server-side, one hostile file becomes a per-connection
DoS.

---

## Phase 0: prerequisites (recommended regardless of the features)

**P0.1 Golden canonical-answer test.** Assert all 28 shipped puzzles' canonical
answers against literals. ~40 lines. Converts every "would this invalidate a
shipped puzzle?" question from a review judgment into a CI failure. Also pins
the load-bearing but undocumented assumption that YAML preserves dict insertion
order, which `signature_first_match` depends on entirely.

**P0.2 Bound simulator inputs.** Upper bounds on `cache.size_lines` and
`len(accesses)`, `storage.requests`, `pipeline.instructions`; explicit
validation of `tlb.tlb_entries > 0` and `page_size > 0` (today those fail only
by an incidental `IndexError`/`ZeroDivisionError`). Model on `packet.py:38`,
which already bounds its loop and explains why. Every shipped puzzle passes with
three orders of magnitude of headroom.

**P0.3 Stop swallowing `MemoryError`.** Re-raise `MemoryError` and
`RecursionError` from `_validate_playable` rather than relabelling them.

**P0.4 Reconcile the contract's fidelity statements with what shipped.** Three
have drifted: the doc's draft `packet` statement promises ARP and link-layer
framing that were never implemented; `signature`'s draft omits the first-match
rule the content depends on; `pipeline`'s draft claims structural hazards it
does not model. Decision 6 makes these statements a contract, so this is a
correctness fix, roughly ten minutes.

Phase 0 is small, independently justified, and unblocks everything below.

---

## Feature A: persist in-flight puzzle state

**Recommended scope (save schema 1.1 → 1.2):**

- `prompted_rooms` (sorted list). **This is the actual fix for "the room
  re-offers its puzzle."** Persisting the active puzzle alone does not fix it:
  `maybe_auto_prompt` bails while a puzzle is active, so re-prompting resumes
  the moment the player answers or skips.
- `current` as a puzzle **id**, plus `hints_used`. Tolerant restore: an id that
  no longer exists → `current = None`, `hints_used = 0`; otherwise clamp
  `hints_used` to `len(puzzle.hints)`.
- Bump `SAVE_SCHEMA_VERSION` to `1.2`, add to `_COMPATIBLE_VERSIONS`, update the
  hard-coded assertion in `test_save_load.py`, and add a "1.1 file still loads"
  test mirroring the existing 1.0 one.

Under 30 lines. It rides the pass-through properties `Game` already exposes,
whose comment says they exist for "commands.py, the save system, and existing
tests."

**Side benefit:** it fixes an existing inconsistency. Hint 2 marks a puzzle
attempted durably, but `hints_used` is lost on load, so today a reload grants
two more free hints on an already-attempted puzzle.

**Never serialize:** the `MicroPuzzle` body, instruction lists, or access
traces. Those are content that must come from disk; storing them turns a save
file into a fork of the game content.

**Minigames: technically easy, low value.** Both simulators turned out to be
pure and the memory minigame already re-derives every verdict from scratch, so a
restored minigame at cycle 7 is byte-identical to one that stepped there. The
design doc's rationale assumed persistence would be costly; it is not. But a
minigame is a scratchpad that restarts in one command and feeds nothing else.
**Recommend deferring**, and if it ships, ship it in the same 1.2 payload so
there is only one bump.

---

## Feature B: higher-fidelity network and security simulators

**Reframing.** These simulators are not inaccurate; they lack *degrees of
freedom*. Every other simulator has a policy knob whose flip changes the answer
on an identical workload (forwarding on/off, LRU/FIFO, FCFS/SSTF, associativity
1/2), and the shipped content is built on that device: `hdd_seek_fcfs` and
`hdd_seek_sstf` share a byte-identical setup and differ only in `algorithm`.
`packet` and `signature` have zero knobs, so their puzzles can only ask the
player to read the setup back. Adding TCP windowing does not fix that.

Also note three of the five "networking" puzzles actually teach interconnect and
DMA, not IP. Their explanations say so. So protocol-axis fidelity is off-theme;
transfer-cost-axis fidelity is on-theme.

**Rule: add new simulators, never edit `packet.py` or `signature.py` in place.**
`SIMULATORS` is a plain dict, so additions cannot perturb existing puzzles.
Their fidelity statements stay accurate and their nine puzzles keep their
answers.

Ranked by teaching value per unit of risk:

1. **False-positive security puzzle. Zero code.** A benign file that legitimately
   contains a signature (the AV database itself, a quarantine log). Answer is a
   virus name on a harmless file. Teaches the base-rate lesson none of the four
   shipped security puzzles touches. One YAML file.
2. **Multi-match scanner** as a *new* simulator reporting every match. The
   existing single-verdict puzzle becomes the deliberate contrast, and its
   explanation already sets this up. Done in place it would invalidate
   `signature_first_match` and break player input, since the CHOICE parser
   rejects multi-token answers.
3. **Wildcard scanner** as a new simulator. Turns `signature_near_miss`'s
   "clean" into a match on the same file, paying off an IOU its explanation
   currently leaves open. Supplies the missing policy knob: exact vs wildcard
   over one identical file.
4. **Link-cost simulator** with a store-and-forward vs cut-through knob, plus
   latency/bandwidth per hop. This is the on-theme networking option: it restores
   the counterfactual device and rhymes with the pipeline lesson the game already
   teaches.

**Reject:** TCP handshake/windowing/congestion (explicitly out of scope,
off-theme, largest model); loss/retransmit/collision (nondeterminism conflicts
with the Simulator purity contract, which the loader enforces by executing every
setup).

**Caveat to surface:** networking already sums to 7.5 knowledge against a cap of
5, security to 6.0. Both areas are past the cap, so new puzzles there add
content without adding progression: a player who solves them sees the same
meter afterwards.

---

## Feature C: author-extensible puzzles

**ANSWERED 2026-08-02 (Michael): no player-authored content.** The
user-directory layer described at the end of this section is closed and will
not be built: no `~/.computerquest/puzzles/` loading, no id namespacing, no
`room:` key, no `source` field. The open question below is settled in favour of
*more puzzles*, authored in-repo.

What survives the answer is the validation CLI, which is repo tooling rather
than player-facing extensibility. **Built 2026-08-02** as
`scripts/validate_puzzles.py`.

**Correction (2026-08-02).** The `answer_kind` claim below, that a mismatch
against the simulator's own `answer_kind` loads cleanly with no error at any
layer, was true when this PRD was written and was fixed hours later by Phase 0
(`e5795bb`, "fix the validator"). The check lives at `registry.py:159` and
raises `PuzzleDataError` naming both kinds. It was repeated as an open defect
after that, from this document rather than from the code. Read the code.

**Open question for Michael, and it changes the scope by an order of
magnitude:** is the goal *player-authored* puzzles, or simply *more* puzzles?

If more puzzles, a validation CLI plus `CONTRIBUTING.md` gets most of the value
with no user-directory loading, no id namespacing, no binding indirection, and
no new security surface. 22 rooms sit at or below 2 of the 3-puzzle cap and
about 8 have none, so the shipped tree has real room to grow.

**Recommended v1 either way: the validation CLI.** `from_directory` already *is*
the validator; the CLI is a thin wrapper that reports errors legibly instead of
crashing the game. It should **print the canonical answer**, which is
the single highest-value line of output: every shipped file hand-writes that in
a comment today, and it is the only way an author can check their prompt matches
their setup.

It should also add the checks the loader cannot do, the most important being
**`answer_kind` must equal the simulator's `answer_kind`**. Today a mismatch
loads cleanly and makes every possible answer wrong forever, with no error at
any layer.

**If player-authored is the goal, add (thin layer on the CLI):** load
`~/.computerquest/puzzles/` alongside the packaged tree; namespace user ids on
collision so a user file cannot shadow a shipped one; an optional `room:` key
appended to `Component.puzzles`, since **binding is currently hardcoded Python
and a puzzle bound nowhere is completely unreachable**; enforce the max-3 cap at
runtime rather than only in tests; and a `source` field on `MicroPuzzle` so
origin is visible.

**Skip the in-game editor** (authoring is multi-paragraph prose; a real editor
beats a terminal REPL). A `playtest <id>` preview is ~20 lines and worth more.

**Web-based authoring is a project in its own right**, and it is the one option
that turns F2's footguns into genuine remote vulnerabilities. Prerequisites
would be non-negotiable: bounded YAML parsing, hard numeric limits, subprocess
execution with a wall-clock timeout, per-session quotas.

---

## Contract amendments required

All three are currently listed "Out of scope". Precedent is decision 7
(adaptive difficulty, 2026-07-31): strike the bullet, add a numbered decision,
note the amendment, record the new sha.

- Feature A: amend `architecture-microquiz.md` "Persistence of in-flight
  puzzles" and, if minigames are included, `design-minigames.md` which
  pre-emptively says "called out here so future-me doesn't re-litigate it". The
  honest amendment text is that the original rationale assumed persistence would
  be costly, and the code shows it is not.
- Feature B: amend the out-of-scope bullet and extend the per-simulator fidelity
  section (decision 6 makes those statements contractual).
- Feature C: amend the author-extensible bullet, keeping "no in-game editor".

Adding a decision changes the contract sha recorded in the ABOUTME headers of
`puzzles/types.py` and `puzzles/__init__.py`; both need updating in the same
commit.

---

## Recommended sequence

1. **Phase 0** (P0.1-P0.4). Small, independently justified, unblocks the rest.
2. **Feature A**, puzzle state only, minigames deferred. Smallest, cleanest,
   one schema bump.
3. **Feature C's CLI**, which is also the authoring tool for Feature B's content.
4. **Feature B**, items 1-4, additive simulators only.
5. Feature C's user-directory layer, only if player-authored is the actual goal.

Each step lands green and is separately shippable.

## Decisions (Michael, 2026-08-01)

1. **Feature C: parked.** Neither player-authored puzzles nor the user-directory
   layer. Sticking with the shipped content model for now. This drops the F2
   security work from "blocker" to "hardening worth doing anyway", since without
   user-supplied content those bounds only guard against authoring typos.
2. **Feature A: puzzle state only.** No minigame persistence, so
   `design-minigames.md` is not amended and its "do not re-litigate" note stands.
3. **Feature B: the free win only.** The false-positive security puzzle, one YAML
   file, no code. The new scanners and the link-cost simulator are not being
   authored now.

   **Amended 2026-08-02 (Michael):** this deferred items 2 to 4 to step 4 of the
   build order below. Describing that later as "deferred by the user" misread a
   sequencing call as a cancellation. Items 2 to 4 are now built:
   `scan_all`, `scan_wildcard`, and `link_cost`, with four puzzles. Contract
   decision 10 records the reasoning. Feature B is complete.
4. **Build order: Phase 0 first**, as its own shippable unit.
5. **Sister repo `kodequest` stays untouched.** Read-only reference only.
