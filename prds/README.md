# PRDs

PRDs live here as numbered markdown files, covering work large enough to need a
written plan and an approval before any code is written. GitHub issues were
disabled when this directory started, which is why it exists; they were enabled
on 2026-08-02 and now carry the smaller, self-contained work. A PRD is a
proposal, not a commitment: nothing here is approved or started unless its
Status line says so, and per the lifecycle rules implementation waits on
approval (Phase 1.3).

Status lines here are load-bearing, and they drifted once already: PRDs 2 to 5
sat marked "backlog (not started)" for a day after all four had shipped and
were live in production. Update the Status line in the same commit that lands
the work.

| # | Title | Status | Origin |
|---|---|---|---|
| 1 | [Persistence, simulator fidelity, author-extensible puzzles](1-three-features.md) | Feature A and B SHIPPED; Feature C closed (no player-authored content) | requested 2026-08-01 |
| 2 | [Progressive hints + difficulty/tutorial modes](2-progressive-hints-difficulty-modes.md) | SHIPPED 2026-08-01 | KubeQuest #50 |
| 3 | [Objectives, progressive reveal](3-objectives-progressive-reveal.md) | SHIPPED 2026-08-01 | KubeQuest #51 |
| 4 | [Web tab completion + per-command help](4-web-completion-and-per-command-help.md) | SHIPPED 2026-08-01 | KubeQuest #52 |
| 5 | [help auto-pagination](5-help-auto-pagination.md) | SHIPPED 2026-08-01 | KubeQuest #53 |

Closed on the issue tracker rather than here: the content-gap sweep of
2026-08-02 (issues #1 to #5), which added the `flash`, `simd` and `interleave`
simulators, fixed a seek puzzle standing in the SSD room, and recorded the
eight rooms that hold no puzzle on purpose.

PRDs 2 to 5 are adapted from the sister project `kodequest` (KubeQuest), which
is the same shape of game teaching Kubernetes. They were rewritten against this
codebase rather than copied: each one cites the specific gap it closes here.

Four KubeQuest PRDs were reviewed and deliberately not adopted:

- **#48 architecture-accurate world.** Already true here. Rooms are
  `cpu_package`, `core1`, the cache levels, `pch`, `pcie_*`, and traversal
  follows the real component graph.
- **#49 AI companion.** Pulls against this game's design. The microquiz redesign
  moved deliberately away from a game that tells you things, and decision 3
  makes hints cost you. A companion offering context-aware nudges would undo
  that. Revisit only as narrative voice, not as a hint channel.
- **#54 per-room ASCII art.** Fits the aesthetic but is 35 rooms of content for
  atmosphere rather than teaching.
- **#55 expansion modules.** Same idea as PRD 1's Feature B, already covered.
- **#56 Proving Ground onboarding.** No analogue; this game has no sandbox mode.
