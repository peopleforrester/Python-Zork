# Architecture Spike. Predict-and-Verify Micro-Puzzles

Companion to `docs/design-minigames.md`. Where that doc designed the two
"deep-end" minigames (CPU pipeline, memory hierarchy), this spike designs the
wider, shallower base: a per-component micro-puzzle attached to each room, where
the player predicts what a small simulated subsystem will do and the game runs
the simulator to verify.

This is the structural implementation of Direction C from the spike at
`~/repos/mrf/mrf-knowledge/game-design/2026-06-22_teaching-games-text-adventure-pivot.md`.
The pedagogical pattern is "predict and verify": the player commits an answer,
the game computes the real answer with a real simulator, the diff is the lesson.

## Author / status

- Author: Michael Forrester
- Status: **decisions called** (drafted 2026-06-22, decisions resolved 2026-06-26)
- Decision rationale: see [Decision rationale](#decision-rationale) at the bottom.

## Decisions (applied to this document)

The six open questions in the original draft are resolved as follows. Rationale and the rejected alternative for each one are in [Decision rationale](#decision-rationale).

1. **Multi-puzzle rooms allowed, capped at three.** A `Component.puzzles: list[str]` can hold up to three puzzle ids; rooms may have zero. Three is enough for "intro / twist / hard mode" without breaking the ninety-second budget per room visit.

2. **Soft difficulty gating.** Difficulty-N puzzles appear in `solve` (no argument) listings only when at least one difficulty-(N-1) puzzle in the same area is solved. They remain loadable by explicit `solve <id>` regardless, so a curious player can skip ahead; the gate is presentation only.

3. **Tiered hints.** First hint per puzzle is free. Second and later hints flag the puzzle as "attempted," so a first-time-correct after a costly hint does not bump knowledge. Puzzle data ships with one or two hints per puzzle, ordered cheap-to-expensive.

4. **Auto-prompt on first visit only.** When the player enters a room for the first time and has not attempted its primary puzzle, the puzzle auto-presents with an explicit "type `skip` to put this aside" prompt. On every subsequent visit, only the `[ puzzle available ]` hint shows in `look`. Behaviour gates on the room's primary puzzle id being in `attempted_puzzles`.

5. **Keep the knowledge cap at 5; weight solves by difficulty.** Each solved puzzle contributes `difficulty * 0.5 + 0.5` to its area (difficulty-1 = 1, difficulty-2 = 1.5, difficulty-3 = 2). The cap stays meaningful (knowledge-5 implies real breadth or depth) without requiring every puzzle in the area to be solved. Extra solves count toward achievements.

6. **Each simulator carries a fidelity statement in its module docstring.** Drafts are committed alongside each module's first commit and become the verdict's authority claim. See [Per-simulator fidelity](#per-simulator-fidelity) below.

The Lifecycle, Snapshot, Save/Load, Tests, and Migration plan sections that follow are written against these decisions.

---

## Design intent

Every component the player can visit becomes a constructionist learning slot.
Instead of "you visited the L1 cache room, here is a paragraph explaining L1
caches, your memory knowledge meter +0.5," the loop becomes:

1. Player enters L1 cache room.
2. The room's description hints at a puzzle (`[ puzzle available: predict cache behavior ]`).
3. Player runs `solve`.
4. The game presents a setup: a cache configuration, a sequence of memory
   addresses, and the question "for each access, will it hit or miss?"
5. Player commits an answer string.
6. The simulator runs the same access pattern through a real LRU cache model
   and produces the canonical hit/miss sequence.
7. The game shows the diff: where the player matched, where they were wrong,
   and a one-paragraph explanation of why the wrong predictions failed.
8. On first-time correct, the player's memory-knowledge meter goes up.

The size target per puzzle is **ninety seconds**. A pop quiz with simulated
feedback, not a Zachtronics-scale puzzle. There are thirty-ish rooms, so the
game has thirty-ish puzzle slots forming a wide, shallow base. The two existing
minigames (CPU pipeline, memory hierarchy) become the deeper-end puzzles that
unlock at higher knowledge levels.

## Why this fits Python-Zork's existing shape

Python-Zork is already a knowledge-gated exploration game. The components, the
five-area knowledge meter, the achievement system, and the per-room
descriptions all stay. What changes is the verb that drives the knowledge meter
up: from "visited" to "demonstrated."

The new infrastructure also has standalone value: the simulators that verify
the player's predictions are the same simulators the deep-end minigames will
need. Building the wider base first means the minigames inherit a working
simulator library rather than each needing to invent its own.

---

## Data model

### MicroPuzzle

```python
@dataclass(frozen=True)
class MicroPuzzle:
    id: str                       # e.g. "l1_cache_lru_basic"
    component_category: str       # "cpu" | "memory" | "storage" | "networking" | "security"
    subject_area: str             # same domain space as Player.knowledge keys
    difficulty: int               # 1-3 (3 is "fluent"); future-proofed for 4-5 deep-end
    title: str                    # one-line label shown in the prompt header
    prompt: str                   # one or two short paragraphs setting up the question
    setup: dict[str, Any]         # parameters handed to the simulator
    answer_kind: AnswerKind       # what shape of answer the player commits
    answer_grammar: str           # one-line hint of the expected input format
    explanation: str              # one or two paragraphs shown after the verify step
```

`setup` is opaque to the puzzle infrastructure. It is the simulator's input
contract. For a cache puzzle, `setup` looks like:

```python
{
    "policy": "LRU",
    "size_lines": 4,
    "line_size_bytes": 64,
    "associativity": 1,
    "accesses": [0x100, 0x140, 0x180, 0x1C0, 0x100, 0x200, 0x140],
}
```

For a pipeline-hazard puzzle, `setup` looks like:

```python
{
    "stages": 5,
    "forwarding": False,
    "instructions": [
        ("LOAD",  ("R1",),       "R2"),
        ("ADD",   ("R2", "R3"),  "R4"),
        ("STORE", ("R4", "R1"),  None),
    ],
}
```

The simulator owns the schema for each category. Puzzle authoring is data, not
code; see [Puzzle data layout](#puzzle-data-layout) below.

### AnswerKind

```python
class AnswerKind(str, Enum):
    CHOICE  = "choice"   # one of N labelled options
    SEQUENCE = "sequence" # ordered list of tokens, e.g. "hit miss miss hit"
    NUMBER  = "number"   # single int
    BOOL    = "bool"     # yes/no
    MAPPING = "mapping"  # k=v pairs, e.g. "n=cpu1 s=l3"
```

Each kind has a small parser that turns a player line into the canonical shape
the simulator's output uses. The parser tolerates whitespace, commas, and
case but is otherwise strict: wrong shape comes back to the player as "I
need an answer like: `hit miss miss hit hit`," not as a wrong answer.

### Simulator interface

```python
class Simulator(Protocol):
    """A category-specific simulator. Pure function from setup → canonical answer."""

    answer_kind: ClassVar[AnswerKind]

    def run(self, setup: dict[str, Any]) -> Any:
        """Return the canonical answer in the shape AnswerKind dictates."""
```

One simulator module per component category, living under
`computerquest/mechanics/simulators/`. The simulator's `run()` is pure: same
setup, same answer, every time. That property is what makes the test
architecture trivial.

Each simulator also owns a small `verify(player_answer, canonical) -> Verdict`
helper that diffs the two and produces structured feedback (which positions
matched, which did not). Generic verify works for most cases; per-simulator
overrides exist for cases where the diff needs domain context (e.g. "you
predicted a miss but the line was evicted by access #4, so it actually missed
for a different reason").

```python
@dataclass(frozen=True)
class Verdict:
    correct: bool                       # full match across the answer
    positions: list[PositionVerdict]    # per-element correctness
    summary: str                        # one-line summary
    deep_notes: list[str]               # optional per-position commentary
```

### Player state additions

```python
# computerquest/models/player.py
self.solved_puzzles: set[str] = set()   # MicroPuzzle.id values
self.attempted_puzzles: set[str] = set() # solved or not, ever shown
```

The knowledge meter formula changes (see [Knowledge meter](#knowledge-meter)
below) but the field shape stays: five subject areas, 0 to 5 each, derived from
puzzles solved in that area's component category.

---

## Module layout

```
computerquest/mechanics/
    minigames/                 # existing: the deep-end puzzles (CPU pipeline, memory hierarchy)
        cpu.py
        memory.py
    puzzles/                   # NEW: micro-puzzle infrastructure
        __init__.py            # exports MicroPuzzle, AnswerKind, Verdict, registry helpers
        types.py               # dataclasses + enum
        parsers.py             # AnswerKind → player-input parser
        registry.py            # loads YAML puzzle files, returns indexed by id and by room
        data/                  # the puzzle content; data only
            cpu/
                core_register_read.yaml
                pipeline_stall_intro.yaml
            memory/
                l1_lru_basic.yaml
                l2_associativity.yaml
                ram_dimm_address_decode.yaml
                tlb_walk_basic.yaml
            storage/
                ssd_block_remap.yaml
                hdd_seek_sequence.yaml
            networking/
                packet_route_lan.yaml
                tcp_flag_sequence.yaml
            security/
                virus_signature_match.yaml
    simulators/                # NEW: pure functions verifying puzzle answers
        __init__.py
        base.py                # Simulator protocol, Verdict dataclass, generic verify()
        cache.py               # LRU/FIFO cache (used by L1/L2/L3 rooms + memory minigame)
        pipeline.py            # 5-stage CPU pipeline (used by core rooms + cpu minigame)
        tlb.py                 # virtual → physical address translation
        packet.py              # simple network routing simulator
        storage.py             # block remapping / seek-time models
        signature.py           # virus signature matching simulator
```

The minigames subpackage is unchanged structurally; both minigames migrate from
returning placeholder strings to consuming `simulators.pipeline` and
`simulators.cache` for their state advancement.

### Why simulators live separately from minigames

Three reasons.

1. **The deep-end minigames and the micro-puzzles need the same simulator.**
   The CPU pipeline minigame and the pipeline-hazard micro-puzzles both ask
   "given these instructions and this hazard policy, what does the pipeline do
   cycle by cycle?" One simulator, two consumers.

2. **The simulators are testable as plain functions.** No Game dependency, no
   Player dependency, no I/O. `pytest` for the simulators is the easiest test
   surface in the whole project.

3. **The simulators are educational artifacts in their own right.** A
   well-commented `simulators/cache.py` is a teaching tool independent of the
   game. Worth maintaining as such.

---

## Puzzle data layout

Each puzzle is a YAML file under `mechanics/puzzles/data/<category>/`. One file
per puzzle so reviews diff cleanly. Shape:

```yaml
# mechanics/puzzles/data/memory/l1_lru_basic.yaml
id: l1_lru_basic
component_category: memory
subject_area: memory
difficulty: 1
title: "L1 Cache: predict hit/miss with LRU eviction"
prompt: |
  You are looking at a 4-line, direct-mapped L1 cache with 64-byte lines and
  an LRU replacement policy. The CPU issues this sequence of byte addresses:
    0x0100  0x0140  0x0180  0x01C0  0x0100  0x0200  0x0140

  For each access, predict whether it will be a hit (H) or a miss (M).

setup:
  policy: LRU
  size_lines: 4
  line_size_bytes: 64
  associativity: 1
  accesses: [0x0100, 0x0140, 0x0180, 0x01C0, 0x0100, 0x0200, 0x0140]

answer_kind: sequence
answer_grammar: "seven tokens of H or M, separated by spaces"

explanation: |
  The first four accesses each go to a different line (0x100, 0x140, 0x180,
  0x1C0). All four are cold misses. The fifth access (0x100) is still in
  cache from access 1, so it hits. The sixth (0x200) maps to the same set as
  0x100; in a direct-mapped cache that means 0x200 evicts 0x100. So 0x200
  misses. The seventh (0x140) was last touched at access 2 and is still
  present, so it hits.

  Direct mapping is brutal: even with LRU, you cannot keep two addresses
  that map to the same set. The next puzzle in this room raises associativity
  to 2 to show how that changes things.
```

Loader walks the data tree at startup, validates each file's `setup` against
the named simulator's schema (by calling `simulator.run(setup)` and catching
exceptions), and indexes the puzzles by `id` and by `component_category`.

### Room ↔ puzzle binding

```python
# computerquest/world/architecture.py additions
self.rooms["core1_l1"].puzzles = ["l1_lru_basic", "l1_associativity_2way"]
self.rooms["ram_dimm1"].puzzles = ["ram_dimm_address_decode"]
```

The binding is declarative in the architecture builder, not derived. That keeps
"which puzzles live in which room" reviewable in one place.

A room may have 0, 1, or many puzzles. Many is common for cache rooms (cold
misses, eviction patterns, associativity comparisons). Zero is fine for purely
connective rooms.

---

## Commands

New verbs added to `CommandProcessor`:

| Verb | Effect |
|---|---|
| `solve` | List puzzles available in the current room, or prompt the topmost unsolved one if exactly one is shown. |
| `solve <id>` | Begin the puzzle with that id (if it's in the current room). |
| `answer <tokens...>` | Commit an answer for the currently-active puzzle. |
| `hint` | Show a one-line hint for the currently-active puzzle. Costs no progress; available always. |
| `skip` | Abandon the current puzzle without recording an attempt. Lets the player walk away. |

State machine inside the Game:

- `current_puzzle: MicroPuzzle | None`: analogous to `current_minigame`.
- Active puzzle persists across rooms; `look` and `move` still work while the
  puzzle is open. The puzzle ends when the player commits an answer (right or
  wrong) or runs `skip`.

Reuse the existing read-only verb set so opening a puzzle doesn't dirty the
save state; committing an answer does.

### Interaction example

```
> look
┏━━━━━━━━━━━━━━━━━━━━ LOCATION ━━━━━━━━━━━━━━━━━━━━━┓
   Core 1 L1 Cache
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
A 64 KB direct-mapped L1 cache feeding Core 1...

[ puzzle available: L1 Cache: predict hit/miss with LRU eviction ]

> solve
You are looking at a 4-line, direct-mapped L1 cache with 64-byte lines...
  0x0100  0x0140  0x0180  0x01C0  0x0100  0x0200  0x0140

Predict each access. Use 'answer H M H M ...' (seven tokens).

> answer M M M M H H H
Verdict:
  position 1 (0x0100): M  ✓ cold miss
  position 2 (0x0140): M  ✓ cold miss
  position 3 (0x0180): M  ✓ cold miss
  position 4 (0x01C0): M  ✓ cold miss
  position 5 (0x0100): H  ✓ still in cache
  position 6 (0x0200): H  ✗ correct answer was M, 0x200 maps to the same
                          set as 0x100 in a direct-mapped cache, so it
                          evicts 0x100 and is itself a cold miss.
  position 7 (0x0140): H  ✓ last touched at access 2, still present.

6 of 7 correct. Memory knowledge unchanged this round; try the room's
follow-up puzzle in this room; it shows how 2-way associativity rescues this case.

(explanation paragraph follows)
```

The first-time-correct rule is "all positions right" for sequence answers. 6/7
counts as an attempt, not a solve. The next attempt isn't penalized: same
setup, same expected answer, same one-shot scoring.

---

## Knowledge meter

Today: `Player.knowledge["memory"]` is 0–5, increments slowly when the player
contacts memory-category components. The contact-based increment is the
instructionist pattern this redesign is moving away from.

New formula:

```
knowledge[area] = min(5, solved_count_in_area)
```

Where `solved_count_in_area` counts unique puzzles in `solved_puzzles` whose
`subject_area` matches. Difficulty multipliers are optional (a difficulty-2
puzzle could count as 1.5) but the first-pass implementation treats every
solve as worth 1.

Floor and ceiling stay at 0–5. The existing knowledge gates (e.g. minigames
require `knowledge[cpu] >= 3`) keep working; they now reflect demonstrated
competence rather than tourism, which is what they were meant to reflect all
along.

The visit-based bonus is **dropped** rather than preserved. Keeping it would
muddle the signal the meter sends both to the player and to the gating logic.

---

## Achievements

The progress system gets new conditions to evaluate:

- `predict_apprentice`: first puzzle of any category solved.
- `predict_journeyman`: every category has at least one solve.
- `predict_master`: every puzzle in any one category solved.
- `predict_grandmaster`: every puzzle in every category solved.
- `cold_streak`: five puzzles solved in a row first-time-correct.

These slot into the existing achievement infrastructure with no schema
changes; only new `Achievement(...)` rows in `ProgressSystem.setup_achievements`.

---

## Save / load

Snapshot adds two fields:

```python
"player": {
    ...
    "solved_puzzles": ["l1_lru_basic", "tlb_walk_basic", ...],
    "attempted_puzzles": [...],
},
```

Current `current_puzzle` is **not** persisted, mirroring the existing
minigame decision. A loaded game starts with no active puzzle. Walking back
into the room presents it again.

Schema version bumps from `1.0` to `1.1`. The loader treats a `1.0` save as
valid but initializes the new fields to empty sets; old saves still load.

---

## Web map integration

`Game.snapshot()` adds per-room state so the React map can color-code:

```python
"rooms": [
    {
        "id": "core1_l1",
        "name": "Core 1 L1 Cache",
        "visited": true,
        "doors": {...},
        "item_count": 0,
        "puzzles": {
            "available": ["l1_lru_basic", "l1_associativity_2way"],
            "solved":    ["l1_lru_basic"],
            "attempted": ["l1_lru_basic", "l1_associativity_2way"],
        }
    },
    ...
]
```

GameMap.tsx gains a CSS class per state, `node solved`, `node attempted`,
`node available`, `node empty`) so the map shows progress at a glance.

---

## Test architecture

Three test layers, each with a clear contract.

### Simulator tests (unit)

For each simulator, a `tests/simulators/test_<name>.py` covers:

- Known-correct inputs from textbook examples (Patterson & Hennessy, Bryant &
  O'Hallaron). Cite the source in the test docstring so the reader can verify.
- Edge cases (empty input, single access, full-eviction sequence).
- Verify generic and per-simulator verify functions on representative answers.

These tests have zero Game dependency. They run in milliseconds.

### Puzzle data tests (validation)

A single `tests/test_puzzle_data.py` walks the puzzle data tree at test time
and, for each puzzle:

- Parses the YAML.
- Resolves the named simulator.
- Calls `simulator.run(puzzle.setup)` and confirms the result is a valid
  answer shape for the puzzle's `answer_kind`.
- Asserts the puzzle's `id` is unique across the whole tree.
- Asserts the `component_category` and `subject_area` fields are in the
  enumerated sets.

This is the "did the author write a wrong puzzle?" gate. New puzzle files
cannot land without this passing.

### Command-flow tests (integration)

`tests/test_microquiz_commands.py`:

- `solve` in a room with no puzzle reports "no puzzle here."
- `solve` in a room with one unsolved puzzle activates it.
- `answer` outside an active puzzle returns "no active puzzle."
- A correct answer flips the puzzle into `solved_puzzles` and increments
  knowledge.
- An incorrect answer records an attempt and shows the verdict but does not
  decrement knowledge.
- `skip` clears the active puzzle without recording an attempt.
- The room's `puzzles` snapshot block reflects the post-answer state.

These exercise the `command_processor.process` → `Game.feed` path that the web
server depends on, so they protect the wire surface too.

---

## Migration plan

The change touches Player, ProgressSystem, the architecture builder, the
command processor, the snapshot, and the React map. Reasonable order:

1. **Simulator scaffolding** (no game integration): add `mechanics/simulators/`
   with `base.py`, `cache.py`, `pipeline.py`. Tests for each. Land
   independently; nothing in the game uses them yet.

2. **Puzzle infrastructure** (no game integration): add
   `mechanics/puzzles/` with types, parsers, registry, and a couple of seed
   YAML files. Validation tests for the data tree. Still nothing user-facing.

3. **Player + architecture wiring**: add `Player.solved_puzzles` and
   `attempted_puzzles`. Bind two or three rooms to puzzle ids in
   `architecture.py`. Snapshot field added. Save/load schema bumped.

4. **Command surface**: add `solve`, `answer`, `hint`, `skip`. Integration
   tests. At this point the game is shippable with three puzzles in three
   rooms.

5. **Content fill**: author the remaining puzzles. Each new YAML file is a
   small PR. Validation tests run on each push.

6. **Knowledge meter cutover**: drop the visit-based knowledge bump. The
   knowledge gates (minigame access, status display) now reflect puzzles
   solved. Some achievements may need adjusting.

7. **Minigames consume simulators**: rewrite the CPU pipeline and memory
   minigames to delegate state advancement to `simulators.pipeline` and
   `simulators.cache`. The minigames stop being placeholders; flip
   `ENABLE_MINIGAMES = True`.

8. **Frontend**: GameMap renders the per-room puzzle state from the snapshot.
   The legend gains four states (empty, available, attempted, solved).

Each step is one or two commits and each gates on its own tests. The order
keeps the game playable at every checkpoint.

## Initial content scope

Thirty rooms across five categories. Target one puzzle per room minimum;
some cache rooms warrant two or three. Realistic first-pass count:

| Category | Puzzles | Notes |
|---|---|---|
| cpu | 8 | core rooms + cache rooms + ALU/CU/registers |
| memory | 7 | L1/L2/L3 sets, RAM, virtual memory, TLB |
| storage | 4 | SSD, HDD, SATA, storage controller |
| networking | 5 | NIC, PCH network paths, packet routing |
| security | 4 | virus signatures, quarantine flow, BIOS signing |
| **total** | **28** | one or two per relevant room |

Each puzzle is roughly one screen of prompt + one screen of explanation. With
the simulator layer doing the verification work, each puzzle is mostly
content authoring rather than code.

## Estimated work

- Simulators: 1 weekend per category (5 categories) = 5 weekends.
- Puzzle data: 30 minutes per puzzle × 28 = 14 hours, spread out.
- Command surface + tests: 1 weekend.
- Knowledge meter cutover + achievements: 1 weekend.
- Minigames consuming simulators: 1 weekend per minigame = 2 weekends.
- Frontend per-room state: half a weekend.

Total order-of-magnitude: two to three months of weekend work, with the game
playable at the end of each weekend along the way. No giant uncommittable
branch.

---

## Out of scope

- **Author-extensible puzzles.** Players cannot write their own puzzles in
  the first pass. The infrastructure supports it (puzzles are data, not
  code), but no in-game editor.
- **Adaptive difficulty.** The puzzle order is room-determined, not
  player-skill-determined. A future pass could re-order based on solve
  history.
- **Multiplayer / leaderboards.** Single-player tool.
- **Persistence of in-flight puzzles.** A loaded game starts fresh; the room
  re-offers the puzzle.
- **Networking and security simulators at production fidelity.** First-pass
  simulators are educationally honest but not full-fidelity (e.g. the network
  simulator routes through PCH, NIC, and an abstracted wire; it does not
  implement TCP window scaling).

## Anti-goals

- **Puzzles as gates that block exploration.** A player who hates puzzles must
  still be able to walk through every room, read the descriptions, and find
  viruses. Puzzles unlock knowledge-meter progression and minigame access; they
  do not gate movement.
- **The simulator becomes the game.** The simulators are verification
  machinery, not the gameplay. The gameplay is "predict, then learn from the
  diff." If a puzzle feels like running a simulator manually, the puzzle is
  designed wrong.
- **Punishment for wrong answers.** Wrong answer = attempt recorded, no
  knowledge penalty, free retry. The lesson is in the explanation, not in
  withholding access.

---

## Per-simulator fidelity

Each simulator module ships with a fidelity statement as a top-of-module docstring. The statement is the verdict's authority claim: when a puzzle's verdict says "actually a miss," the player can read the simulator's fidelity statement to know exactly what model that verdict came from. First-pass drafts:

### `simulators/cache.py`

> Educational cache simulator. Models direct-mapped and set-associative caches with configurable line size, associativity, and replacement policy (LRU and FIFO). Lines are addressed by tag and index; valid bits are tracked. NOT modeled: MESI or any other coherence protocol; hardware prefetching; write buffers; multi-level inclusion or exclusion; non-power-of-two cache sizes; trace-driven warmup. Verdicts assume a cold cache at the start of each puzzle.

### `simulators/pipeline.py`

> Educational 5-stage CPU pipeline simulator (IF, ID, EX, MEM, WB). Models in-order issue, RAW data hazards with configurable stall or forward resolution, and structural hazards on shared resources. NOT modeled: branch prediction, speculative execution, out-of-order execution, register renaming, superscalar issue, control hazards from real branches (every puzzle is straight-line code), or any hazard beyond RAW. Verdicts cite the textbook MIPS pipeline (Patterson & Hennessy).

### `simulators/tlb.py`

> Educational virtual-to-physical translation simulator. Models a single-level page table with 4KB pages and a fully-associative TLB with configurable size and replacement policy. Translation walks the page table on a miss; the TLB caches the result. NOT modeled: multi-level page tables; huge or transparent huge pages; TLB shootdown across cores; ASIDs or process tagging; PCID. Verdicts cite the textbook x86 paging model.

### `simulators/packet.py`

> Educational network routing simulator. Models OSI layers 1 to 3: link-layer framing, IP routing through a small static topology, ARP resolution against a fixed table. NOT modeled: TCP windowing, congestion control, retransmit, NAT, firewall policy, MTU fragmentation, IPv6, or any wireless effect. Verdicts assume a quiet, lossless wire.

### `simulators/storage.py`

> Educational block-storage simulator. Models block-level reads and writes, a flat LBA space, a simple HDD seek model (track-to-track distance contributes to access time), and an SSD block-remap counter. NOT modeled: SSD garbage collection, write amplification, wear leveling beyond the remap count, NCQ, command queuing depth effects, controller-cached writes. Verdicts cite the textbook HDD geometry and the abstract SSD model from Bryant and O'Hallaron.

### `simulators/signature.py`

> Educational virus-signature matching simulator. Models exact-pattern matching against a curated signature list. The "found virus" verdict comes from matching a file's contents against the canonical signature for that virus. NOT modeled: heuristic detection, behavior monitoring, polymorphic-virus dynamic matching, sandbox emulation. Verdicts say "this matches the canonical signature for X"; they do not say "this is, in the world, a virus."

Each fidelity statement is a contract. If a puzzle's verdict relies on behaviour the statement excludes, either the puzzle is wrong or the statement needs amending. Both cases are reviewable.

---

## Decision rationale

Rationale and rejected alternatives for the six calls at the top of this document.

### 1. Multi-puzzle rooms (capped at three)

The single-puzzle alternative kept room rhythm uniform but wasted content space in rooms with natural complexity layers (L1 cache → direct-mapped, then 2-way set-associative, then write policies). Three caps the depth before any one room becomes a Zachtronics level and breaks the ninety-second budget. The `Component.puzzles: list[str]` model already supports it; this decision is purely a content-authoring policy.

### 2. Soft difficulty gating

Hard gating respected the learning curve at the cost of player agency. Open ordering preserved agency at the cost of presenting TLB-walk puzzles to a player who has not seen basic cache misses yet. Soft gating splits the difference: by default the `solve` listing shows only difficulty-appropriate puzzles in the room, but a curious player who reads ahead can still `solve <id>` directly. The gate is on the listing UI, not on the engine. Standard pattern from puzzle games with difficulty curves (Sigmar's Garden, the Witness, several Zachtronics entries).

### 3. Tiered hints

Free unlimited hints minimized frustration but let players walk through every puzzle on hints and still see their knowledge meter rise. Costly hints (any hint flags the puzzle attempted) preserved honest measurement at the cost of punishing the player who genuinely just needs the setup re-stated. Tiering keeps both properties. First hint is "I'm stuck on what the puzzle is asking", a free re-statement. Second and later hints are "this concept is what's tested", they start to give the shape of the answer away, and a first-time-correct after those does not bump knowledge. Puzzle YAML files declare hints as an ordered list; the engine assumes the first is free, the rest are not. Authors can decide whether to ship one cheap hint, one cheap and one costly, or no hints at all.

### 4. Auto-prompt on first visit only

Auto-prompting every visit is the Khan Academy / Duolingo pattern: aggressive teaching, intrusive in an exploration game. Prompt-on-look only is gentle but easy to skip past entirely, a player can wander the whole map, hit `look` thirty times, and never notice the game has a puzzle layer. First-visit-only auto-prompt lands in the middle: the puzzle is presented once as a clear first impression of the room, with a one-key escape (`skip`). Subsequent visits respect the player's choice and offer the puzzle as a hint in the `look` output. The behaviour gates on `room.puzzles[0] in attempted_puzzles`, so `skip` flips the gate without recording a real attempt.

### 5. Cap at 5, weight by difficulty

Raising the cap (say to 10) would have made cap mean less and made `knowledge >= 3` gates harder to reason about. Counting every solve as 1 would mean a player who only solves the easy puzzles caps out before seeing anything hard. The difficulty weight (`difficulty * 0.5 + 0.5`) keeps the cap meaningful as a real competence indicator: a knowledge-5 player has either breadth (5+ easy solves) or depth (3 hard solves). Knowledge gates retain their existing semantics. Extra puzzles become content for the achievement system (`predict_master`, `predict_grandmaster`) without distorting the meter.

### 6. Per-simulator fidelity statements

The temptation is to either over-engineer the simulators (production-fidelity for everything) or under-engineer them and hope no one notices. Neither is honest. Each simulator's fidelity statement makes the verdict's authority claim explicit. When a player asks "but what about MESI coherence?" the cache simulator's docstring answers: "not modeled here; the verdict is correct for the configuration we do model." That makes Python-Zork an honest teaching artifact instead of a black box that returns answers nobody can verify. The statements above are first-pass drafts, each will be revisited when the corresponding simulator is implemented and may tighten or loosen based on what the puzzle content actually needs.
