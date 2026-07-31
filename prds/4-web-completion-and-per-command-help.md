# PRD 4: Tab completion in the web terminal + per-command help

Status: **backlog** (not started, not approved)
Adapted from KubeQuest PRD #52.

## Why

Two verified gaps, both on the surface where the game is actually played.

**Completion exists, but only in the CLI.** `Game.setup_readline` registers a
readline completer covering command names, direction words, room items, and
inventory items, with a special case narrowing `take`/`get` to room items. It is
genuinely good. It is also unreachable from the browser, because readline is a
terminal library and the web client is xterm.js talking to the socket. The
deployed game, which is how the game is normally played, has no completion at
all.

**Per-command help does not exist.** `HelpCommand.execute` ignores its arguments
entirely and returns the full screen, so `help scan` prints all 71 lines rather
than explaining `scan`. The full help does list every command with a one-line
description, so the content is there; there is no way to ask for one entry.

## Requirements

- **Completion in the web terminal**, covering the same candidates the readline
  completer already handles: commands, directions, room items, inventory items,
  and puzzle ids after `solve`.
- **Server-side candidate generation.** The client must not hold a copy of the
  command table or the room's contents; both already exist server-side and the
  snapshot already carries room state. A new socket event returning completions
  for a partial line keeps one source of truth.
- **Per-command help**: `help <command>` returns that command's entry plus a
  short example. Unknown names should suggest near matches, reusing the existing
  prefix matcher rather than adding a second fuzzy path.
- Completion and help must both stay read-only and consume no turn.

## Design notes

`Game._match_prefix` already resolves an abbreviation against a candidate list
and is used for commands, room items, and inventory items. Completion is the
same problem returning all matches instead of the unique one, so the candidate
sources can be shared rather than duplicated.

Watch the input path: the server buffers keystrokes per session and flushes on
newline, with a per-event cap and coalesced echo. Tab is currently dropped along
with other non-printable input. Handling it means adding a branch in that loop
and emitting a completion rather than an echo, without weakening the input caps.

## Deliverable

Tab completion working in the deployed web terminal against server-generated
candidates, `help <command>` returning a single entry, and tests covering
candidate generation and the unknown-command suggestion path.
