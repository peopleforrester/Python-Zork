# PRD 5: help auto-pagination

Status: **SHIPPED** 2026-08-01. `server.py::paginate` pages reference output to
the reported terminal height. Later fixes: a command typed at `--more--` runs
instead of being swallowed, and Ctrl-C cancels the pager rather than leaving it
armed behind a fresh prompt.
Adapted from KubeQuest PRD #53.

## Why

`help` returns 71 lines in one emit. The web terminal renders roughly 39 rows in
its viewport, so more than half the screen scrolls past before the player can
read it, and the top of the box, including the movement and exploration
sections, is what gets lost.

This was hit directly while testing the deployed build: reading the rendered
terminal via the DOM returned only the visible rows, because xterm.js
virtualises its buffer. The same truncation a probe sees is what a player sees.

The quick reference behind `?` is shorter but has the same shape, and the ASCII
map is 76 lines, comfortably past a viewport too.

## Requirements

- **Paginate long output to the terminal height**, with a `--more--` style
  continuation, rather than emitting one long block.
- **Height comes from the client.** The server has no idea how tall the terminal
  is. The web client knows its xterm dimensions and the CLI can ask the tty, so
  the size must be reported to the server, most naturally on `start_game` and on
  resize.
- **Degrade safely.** With no reported height, fall back to emitting everything,
  which is today's behaviour. Pagination must never be able to strand a player
  mid-page with no way forward.
- **Apply to any long output, not just help**: the map and the motherboard
  diagram have the same problem.
- Paging input must not be mistaken for a game command, and must respect the
  existing per-event input caps.

## Design notes

Pagination is a presentation concern, so it belongs at the emit boundary in the
server rather than inside `content/help.py`. Keeping the content functions
returning whole strings preserves the golden-output tests that pin help, welcome
and every about-topic byte for byte; a paginator that splits at the emit step
leaves those assertions valid.

The CLI path prints directly and would need its own small pager, or can keep
today's behaviour, since a real terminal scrollback already solves it there. The
web client is where the problem actually bites.

## Deliverable

Long output paginated to the reported terminal height in the web client, with a
documented fallback when height is unknown, and tests covering the split
boundaries and the no-height path.
