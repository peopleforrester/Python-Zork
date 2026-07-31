# PRD 3: Objectives — progressive reveal, grouped by location

Status: **backlog** (not started, not approved)
Adapted from KubeQuest PRD #51 (inverted: that game shows too many objectives,
this one shows none).

## Why

There is no objectives command. `status` reports virus counts, `progress` and
`achievements` report score, and `knowledge` reports the meters. None of them
answers the question a player actually has, which is what to do next.

Observed directly while playing the deployed build to completion: the only
reason the route to all five viruses was efficient is that the virus locations
were read out of `architecture.py`. A player without source access has to `scan`
in up to 35 rooms to find five viruses, with no in-game signal narrowing the
search. The welcome text states the mission once and never mentions it again.

Puzzles are better served, since `look` appends `[ puzzle available: <title> ]`,
but nothing aggregates that. A player cannot ask which rooms still hold unsolved
puzzles without walking back through all of them.

## Requirements

- An **objectives** command showing the next few steps rather than a full dump.
- **Grouped by location or zone**, using the room graph that already exists.
- **Progressively revealed.** Early objectives point at exploration and the
  first puzzles; virus-hunting detail appears as the player acquires the means
  to act on it. The antivirus tool is already in the starting inventory, so the
  gate is knowledge and exploration, not equipment.
- **Derived, never hand-maintained.** Objectives must be computed from live
  state (`found_viruses`, `quarantined_viruses`, `solved_puzzles`, room
  `visited` flags, room puzzle bindings). A hand-written list would drift from
  content the way the puzzle answer comments did.
- Read-only. Listing objectives must not consume a turn or alter puzzle state.

## Design notes

The data is all present. `Game.snapshot()` already assembles per-room visited
state, item counts, and per-room puzzle available/solved/attempted sets for the
web map. An objectives view is largely a different projection of that same
snapshot, which also means the web client could render it without new server
work.

Care is needed not to spoil the search: the point of `scan` is that finding a
virus is an act of investigation. Objectives should narrow the space (for
example naming a subsystem or an unvisited region) rather than naming the room
holding the virus.

## Deliverable

An `objectives` command, computed from live state, showing a small ordered set
grouped by location, plus tests pinning that it reveals progressively and never
names an unfound virus's exact room.
