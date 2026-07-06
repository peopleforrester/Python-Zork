# Minigame Design. CPU Pipeline & Memory Hierarchy

Pre-work for Step 4.1 (`tk-a7098e`). The minigames are currently no-op stubs
gated behind `config.ENABLE_MINIGAMES = False` (Step 1.3). This document
specifies what they should do once implemented, so the implementation work
has concrete targets and the eventual UX matches the educational intent of
the rest of the game.

Scope: two minigames only. CPU pipeline and memory hierarchy. The plan does
not call for networking, storage, or security minigames; those would be
separate proposals.

## Author / status

- Author: Michael Forrester
- Status: **draft for review** (2026-06-10)
- Decisions still open: see [Open decisions](#open-decisions) at the bottom.

---

## Design constraints

The minigames have to fit inside the existing game's shape:

1. **Text-only.** The game is a CLI text-adventure. No graphics, no animation
   beyond redrawn ASCII frames. Anything described here renders in a
   terminal with ANSI colour and Unicode box-drawing characters.
2. **Knowledge-gated.** A player can only start a minigame after reaching
   knowledge level 3 in the relevant area (`player.knowledge["cpu"]` /
   `["memory"]`). The gating is already in `Game.start_*_minigame()`.
3. **Existing command surface.** Players control minigames through the same
   `simulate` verb the rest of the game uses. The current verbs are `cpu`,
   `memory`, `step`, `toggle`, `reset`, `stop`. New verbs can be added but
   should stay in the `simulate <action>` namespace.
4. **Single active minigame.** `Game.current_minigame` is a single slot.
   Starting a new minigame replaces the existing one. `simulate stop`
   clears it.
5. **No new dependencies.** Stdlib only. The educational goal doesn't
   benefit from a simulation framework or a TUI library.
6. **Persistence-aware.** Save/load (now live as of `tk-24fa9f`) snapshots
   the player and world but not active minigame state. A loaded game starts
   with no active minigame. This is a deliberate simplification: minigames
   are short interactive sessions, not long-running state worth persisting.

## CPU Pipeline Minigame

### Educational objectives

By the end of the minigame, a player who started with
`knowledge["cpu"] >= 3` should be able to:

1. Name the five canonical pipeline stages (IF, ID, EX, MEM, WB) and what
   each does.
2. Explain why pipelining improves **throughput** without improving
   per-instruction **latency**.
3. Identify a **data hazard** (read-after-write) on a small instruction
   trace, and explain why it forces a stall.
4. Distinguish a stall (insert a bubble) from forwarding (route the EX
   result back without waiting for WB).

These are the canonical concepts in any intro computer-architecture course
(Patterson & Hennessy chapter 4, Bryant & O'Hallaron chapter 4). The game
already teaches the components informally via `about cpu`; the minigame
provides the active reinforcement.

### State model

```
PipelineState
    cycle:       int              # cycles elapsed since start
    workload:    list[Instruction] # the canned trace
    issued:      int              # next instruction to enter IF
    stages:      tuple[Instruction | None, ...]  # length 5; (IF, ID, EX, MEM, WB)
    pipelined:   bool             # False -> one stage at a time
    completed:   int              # instructions retired
    hazards:     list[HazardEvent]  # for the post-game debrief
    mode:        Mode             # Mode.RUNNING | Mode.FINISHED
```

`Instruction` is a small dataclass: opcode (str), src (tuple[str, ...] for
register names), dst (str | None), and the cycle it entered IF (filled in at
issue time). Six to ten instructions per canned workload: enough to show a
hazard, short enough to finish in under a minute of player input.

### Learning loop

1. **Explain.** `simulate cpu` prints a one-screen overview: the five stages,
   the workload as a list of instruction strings, the current mode
   (pipelined by default), and the prompt for the next action.
2. **Step.** `simulate step` advances exactly one cycle:
   - Pipelined mode: each stage's instruction moves right; IF pulls the
     next instruction from the workload (if any); WB retires the current
     occupant and increments `completed`.
   - Non-pipelined mode: a single instruction occupies one stage at a time,
     traversing all five stages before the next instruction can issue.
   - Hazard detection runs before the move. If `IF→ID` would read a
     register currently being written by an instruction in `EX/MEM/WB`,
     either insert a stall (a bubble fills `ID`, the IF instruction holds)
     or forward (advance normally and record a `HazardEvent` for the
     debrief). Whether to stall or forward is a player setting, see below.
3. **Render.** After every `step`, render the pipeline as a 5-column box
   diagram with the current occupant of each stage (or `--bubble--`),
   the cycle counter, the throughput so far (completed / cycle), and a
   short status line about what just happened (issued, retired, stalled,
   forwarded).
4. **Toggle.** `simulate toggle` flips `pipelined`. The reset is partial -
   the workload restarts but the player's mode choice persists so they can
   compare the two timelines side by side. The minigame remembers the
   prior pipelined-mode finish cycle so the toggle prompt can say
   "your pipelined run finished in N cycles; now run non-pipelined to
   compare".
5. **Forwarding.** `simulate forward` toggles a `forwarding_enabled` flag
   (default off when the minigame starts). With forwarding off, hazards
   stall. With it on, hazards forward and the throughput improves. This is
   the third learnable variable.
6. **Finish.** When all instructions have retired, the minigame enters
   `Mode.FINISHED` and prints a debrief:
   - Total cycles, throughput (instructions/cycle), and stall count.
   - The instruction-by-instruction Gantt diagram for review.
   - A "what changed?" diff vs the prior run if the player switched modes.
   - The minigame stays loaded until `simulate stop` or `simulate reset`.

### Commands

| Verb | Effect |
|---|---|
| `simulate cpu` | Start the minigame (or report knowledge requirement). |
| `simulate step` | Advance one cycle. |
| `simulate toggle` | Flip pipelined / non-pipelined; restart workload. |
| `simulate forward` | Flip stall / forwarding hazard handling. |
| `simulate reset` | Reset to cycle 0 keeping current mode/forwarding choices. |
| `simulate stop` | Exit the minigame. |
| `simulate status` | Re-render current state without advancing. |

`simulate status` is new; it makes the existing UI patterns consistent -
players type it when they got lost in the prompt history.

### Workload

The canned workload lives in `mechanics/minigames/cpu_workload.py` (new) so
it can be edited independently. A first pass:

```python
WORKLOAD = [
    Instruction("LOAD",  ("R1",),    "R2"),   # MEM-heavy
    Instruction("ADD",   ("R2", "R3"), "R4"), # data hazard on R2
    Instruction("LOAD",  ("R5",),    "R6"),
    Instruction("MUL",   ("R4", "R6"), "R7"), # depends on prior ADD result
    Instruction("STORE", ("R7", "R1"), None),
    Instruction("ADD",   ("R8", "R9"), "R10"),
]
```

Two designed hazards (R2 between insts 0/1, R4/R7 between 1-2-3) so the
player has to confront the stall-vs-forward choice; instruction 5 is
hazard-free so the player can see clean issue/retire after the debriefing
material is set.

### Exit criteria (Step 4.1)

- `simulate cpu` starts the minigame for a qualified player; sub-3
  knowledge still shows the existing gate message.
- All seven verbs above behave per the spec.
- A walk-through of the canned workload at default settings reaches
  `Mode.FINISHED` in the cycle count derived from the design (target:
  10 cycles pipelined-with-forwarding, 13 pipelined-with-stalls,
  30 non-pipelined). These cycle counts are the regression assertions.
- Tests cover: gate, full pipelined-with-stalls run, forwarding toggle
  changes hazard handling, toggle to non-pipelined restarts cleanly,
  stop clears `current_minigame`.

---

## Memory Hierarchy Minigame

### Educational objectives

By the end, a player should be able to:

1. Name the levels of the canonical memory pyramid and roughly order them
   by latency: Registers → L1 → L2 → L3 → RAM → SSD.
2. Predict whether a given access pattern will hit or miss in a small
   cache, given the cache size and associativity.
3. Distinguish **temporal locality** (re-using a recent address) from
   **spatial locality** (accessing an address near a recent one).
4. Explain why an access pattern that exceeds the working set causes
   thrashing.

### State model

```
HierarchyState
    cycle:        int
    workload:     list[int]         # the access pattern (addresses)
    cursor:       int               # next access to issue
    caches:       list[CacheLevel]  # L1, L2, L3
    ram_size:     int               # main memory always hits
    total_cycles: int               # cumulative simulated latency
    hits:         dict[str, int]    # level -> hit count
    misses:       dict[str, int]
    mode:         Mode
```

A `CacheLevel` carries `name`, `size_lines`, `line_size`, `latency_cycles`,
`policy` (`LRU` to start; `FIFO` as a future toggle), and the current
contents (an ordered list of addresses for LRU bookkeeping).

### Learning loop

1. **Explain.** `simulate memory` prints the hierarchy as a vertical stack
   (Registers ░ on top down to RAM at the bottom), with each level's size
   and latency. Lists the canned workload, current cache sizes, and the
   prompt.
2. **Step.** `simulate step` issues the next access. The simulator walks
   the hierarchy top-down: hit at the highest level whose contents include
   the line containing the address; otherwise miss-down to the next level.
   On a miss, eviction policy decides what gets displaced. The cumulative
   latency adds the chosen level's `latency_cycles`.
3. **Render.** The hierarchy stack lights up the level that hit (green) and
   the levels that missed (red); the access-pattern strip below underlines
   the current cursor. A one-line summary tells the player "hit at L2;
   evicted line X from L1; total latency: N cycles."
4. **Pattern selection.** Before stepping, the player can pick the access
   pattern with `simulate pattern <name>`:
   - `sequential`: addresses 0..K, demonstrates spatial locality.
   - `loop`: repeated short cycle, demonstrates temporal locality.
   - `random`: uniform, demonstrates thrashing.
   - `stride`: fixed stride > line size, demonstrates the limits of
     spatial prefetch.
5. **Cache tuning.** `simulate cache <level> <size>` lets the player
   double/halve a level's size (within reason) and re-run to see the hit
   rate change. Doing this requires `knowledge["memory"] >= 4`; otherwise
   the level sizes are read-only.
6. **Finish.** When the workload is exhausted, debrief: total latency,
   per-level hit rate, identified locality patterns. If the player ran more
   than one configuration in a session, diff against the previous best.

### Commands

| Verb | Effect |
|---|---|
| `simulate memory` | Start the minigame (or report knowledge requirement). |
| `simulate step` | Issue the next access. |
| `simulate pattern <name>` | Switch the canned access pattern. |
| `simulate cache <level> <size>` | Tune a cache size (knowledge≥4). |
| `simulate reset` | Re-run with current settings. |
| `simulate stop` | Exit the minigame. |
| `simulate status` | Re-render without advancing. |

### Exit criteria (Step 4.1)

- Gate honours `knowledge["memory"] >= 3`; tuning gated by `>= 4`.
- All four patterns produce distinct, predictable hit-rate profiles on
  the default cache config (target ranges committed as test assertions
  rather than exact values; the policy choice gives a small range).
- LRU policy verified against a canonical Patterson sequence.
- Tests cover: gate, each pattern's expected behaviour, cache-tuning gate,
  reset preserves configuration, stop clears `current_minigame`.

---

## Module layout (Step 4.1 deliverable)

```
computerquest/mechanics/minigames/
    __init__.py            # re-exports both classes (unchanged interface)
    cpu.py                 # CPUPipelineMinigame implementation
    cpu_workload.py        # canned WORKLOAD + Instruction dataclass
    memory.py              # MemoryHierarchyMinigame implementation
    memory_patterns.py     # canned access patterns
    _common.py             # Mode enum, shared rendering helpers
```

The placeholder methods on the current stubs map onto the new
implementations cleanly: `explain` / `get_status` / `step` / `reset` keep
their signatures so `Game.handle_simulation` doesn't need to know about
new verbs at a structural level; it can dispatch them generically by
mapping `verb` → method name.

`SimulateCommand` already short-circuits cpu/memory when
`ENABLE_MINIGAMES` is False. Step 4.1's last action is to flip that flag
to True in `config.py` after the implementations land and tests pass.

---

## Out of scope

- **Saving minigame state.** Active minigame is in-memory only. A
  loaded game starts with `current_minigame = None`. Stated above; called
  out here so future-me doesn't re-litigate it.
- **Multiplayer / leaderboards.** Single-player educational tool.
- **Animation.** No frame-rate-driven rendering. Player input drives every
  redraw via `simulate step`.
- **Configurable workloads.** The workloads are canned. Letting players
  author their own is a separate feature.
- **Networking and security minigames.** Two minigames only.

---

## Open decisions

1. **Hazard handling default.** Forwarding off (so stalls show
   prominently) or on (so throughput looks good from cycle 1)? Current
   draft: **off** because the stall is the more important concept; the
   forwarding payoff is the "aha" moment.
2. **Memory cache tuning permission.** Currently drafted as requiring
   `knowledge["memory"] >= 4`. Alternative: leave open and let the player
   experiment regardless. Trade-off is between giving the player agency vs
   structuring the learning curve.
3. **Achievement integration.** Should completing each minigame unlock an
   achievement (`pipelined_thinker`, `cache_hit_streak`)? The progress
   system already has the slot; just needs an entry. Draft says yes.
4. **`simulate status` retroactive add.** The verb is genuinely useful in
   the placeholder world too. Worth adding it in a small follow-up
   regardless of when 4.1 lands.

Resolve these before starting implementation; each decision changes test
assertions.
