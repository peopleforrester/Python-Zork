# ABOUTME: Persistent save/load for game state. Ported from archive/saveload.py.
# ABOUTME: Step 1.2 removed the no-op stub; tk-24fa9f restores a real impl.

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from computerquest.config import SAVE_DIR
from computerquest.mechanics.puzzles.session import HintMode

# Bump when the on-disk schema changes in a way old saves can't be read.
# 1.1 adds player.solved_puzzles / attempted_puzzles; 1.0 saves still load
# (the new fields default to empty).
# 1.2 adds puzzle_session (active puzzle id, hints used, prompted rooms);
# 1.0 and 1.1 saves still load, restoring an empty session.
# 1.3 adds puzzle_session.hint_mode; older saves restore the standard bargain.
SAVE_SCHEMA_VERSION = "1.3"
_COMPATIBLE_VERSIONS = frozenset({"1.0", "1.1", "1.2", SAVE_SCHEMA_VERSION})


def _default_save_root() -> Path:
    """Resolve the save root under the user's home directory."""
    return Path.home() / SAVE_DIR / "saves"


class SaveLoadSystem:
    """Reads and writes game state to JSON files under ~/SAVE_DIR/saves/.

    The serializer captures: game-level state (turns, victory flags),
    player state (location id, inventory, health, knowledge, virus tallies),
    and per-component state (items, visited, error/power). Component
    structure (names, doors, etc.) is built from architecture.py on every
    load — only mutable runtime state is persisted.
    """

    def __init__(self, game: Any, save_root: Path | None = None) -> None:
        self.game = game
        self.save_root: Path = save_root if save_root is not None else _default_save_root()
        self.save_root.mkdir(parents=True, exist_ok=True)

    # --- Helpers -----------------------------------------------------------

    def _save_path(self, save_name: str) -> Path:
        if not save_name.endswith(".json"):
            save_name = f"{save_name}.json"
        return self.save_root / save_name

    def _serialize(self, save_name: str) -> dict[str, Any]:
        player = self.game.player
        puzzles = self.game.puzzles
        state: dict[str, Any] = {
            "version": SAVE_SCHEMA_VERSION,
            "timestamp": time.time(),
            "save_name": save_name,
            "turns": self.game.turns,
            "player": {
                "location": player.location.id,
                "items": player.items,
                "health": player.health,
                "name": player.name,
                "found_viruses": player.found_viruses,
                "quarantined_viruses": player.quarantined_viruses,
                "knowledge": player.knowledge,
                "solved_puzzles": sorted(player.solved_puzzles),
                "attempted_puzzles": sorted(player.attempted_puzzles),
            },
            "components": {
                room.id: {
                    "items": room.items,
                    "visited": room.visited,
                    "error_state": getattr(room, "error_state", None),
                    "power_state": getattr(room, "power_state", "on"),
                }
                for room in self.game.game_map.rooms.values()
            },
            "game_state": {
                "game_over": self.game.game_over,
                "victory": self.game.victory,
                "all_viruses_found": self.game.all_viruses_found,
            },
            # Schema 1.2. Only the active puzzle's *id* is stored: the body is
            # content that must come from disk, or a stale save could resurrect
            # a puzzle that has since been deleted or rewritten.
            "puzzle_session": {
                "current": puzzles.current.id if puzzles.current else None,
                "hints_used": puzzles.hints_used,
                "prompted_rooms": sorted(puzzles.prompted_rooms),
                # Schema 1.3 (decision 9). A player preference, so an older
                # save simply restores the standard bargain.
                "hint_mode": puzzles.hint_mode.value,
                "struggled": sorted(puzzles.struggled),
            },
        }
        return state

    # --- Public API --------------------------------------------------------

    def save_game(self, save_name: str | None = None) -> str:
        """Persist the current game state. Returns a user-facing message."""
        if not save_name:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            save_name = f"kodekloud_quest_save_{timestamp}"

        path = self._save_path(save_name)
        try:
            state = self._serialize(save_name)
            path.write_text(json.dumps(state, indent=2))
        except OSError as exc:
            return f"Error saving game: {exc}"
        return f"Game saved to {path.name}"

    def load_game(self, save_name: str) -> str:
        """Restore game state from a save file. Returns a user-facing message."""
        path = self._save_path(save_name)
        if not path.exists():
            return f"Save file '{path.name}' not found."

        try:
            state = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            return f"Error loading game: {exc}"

        if state.get("version") not in _COMPATIBLE_VERSIONS:
            return "Save file is from an incompatible game version."

        try:
            self._apply(state)
        except KeyError as exc:
            return f"Save file is missing required field: {exc}"

        return f"Game loaded from {path.name}"

    def _apply(self, state: dict[str, Any]) -> None:
        """Mutate self.game in place to match the deserialized state.

        Every field is read up front, before anything is written. Reading and
        writing in one pass meant a save that was valid down to its last key
        left the player moved, healed, and re-inventoried by the half that had
        already run, so a rejected load was more destructive than no load.
        """
        game = self.game
        rooms_by_id = {room.id: room for room in game.game_map.rooms.values()}

        # --- read and validate, mutating nothing ---
        turns = state["turns"]
        game_state = state["game_state"]
        game_over = game_state["game_over"]
        victory = game_state["victory"]
        # all_viruses_found is derived from player.found_viruses (restored
        # below), so there is nothing to read here. The key is still written
        # on save for schema stability and simply ignored on load.

        player_state = state["player"]
        location = rooms_by_id.get(player_state["location"])
        if location is None:
            raise KeyError(f"unknown location id {player_state['location']!r}")
        items = player_state["items"]
        health = player_state["health"]
        name = player_state["name"]
        found_viruses = player_state["found_viruses"]
        quarantined_viruses = player_state["quarantined_viruses"]
        # Absent in 1.0 saves; default to empty rather than failing.
        solved_puzzles = set(player_state.get("solved_puzzles", []))
        attempted_puzzles = set(player_state.get("attempted_puzzles", []))
        # player.knowledge is deliberately not read: it is derived from the
        # solved set (decision 5) and is rederived below. The file still
        # carries it for readability and for older loaders.

        rooms_to_apply = []
        for room_id, room_state in state["components"].items():
            room = rooms_by_id.get(room_id)
            if room is None:
                continue  # Saved component no longer exists in current world.
            rooms_to_apply.append((room, room_state["items"], room_state["visited"],
                                   room_state.get("error_state"),
                                   room_state.get("power_state", "on")))

        # --- write ---
        game.turns = turns
        game.game_over = game_over
        game.victory = victory

        player = game.player
        player.location = location
        player.items = items
        player.health = health
        player.name = name
        player.found_viruses = found_viruses
        player.quarantined_viruses = quarantined_viruses
        player.solved_puzzles = solved_puzzles
        player.attempted_puzzles = attempted_puzzles
        self.game._recompute_knowledge()

        # Schema 1.2. Restored after the location above, because the session
        # reads player.location. Absent in 1.0 and 1.1 saves, which restore an
        # empty session exactly as before.
        self._apply_puzzle_session(state.get("puzzle_session", {}))

        for room, room_items, visited, error_state, power_state in rooms_to_apply:
            room.items = room_items
            room.visited = visited
            if hasattr(room, "error_state"):
                room.error_state = error_state
            if hasattr(room, "power_state"):
                room.power_state = power_state

        # No map_grid sync needed: it is a derived view over room.visited,
        # which was just restored above.

        if hasattr(game, "progress"):
            game.progress.update()

    def _apply_puzzle_session(self, blob: dict[str, Any]) -> None:
        """Restore in-flight puzzle state, tolerating content drift.

        Puzzles are YAML on disk and change far more often than code, so a save
        can name a puzzle that no longer exists. That is not a reason to refuse
        the whole save: this follows the loader's existing precedent of skipping
        unknown component ids rather than raising. Unknown prompted rooms are
        inert for the same reason, being just keys that no longer match.
        """
        session = self.game.puzzles
        registry = self.game.puzzle_registry

        puzzle_id = blob.get("current")
        puzzle = registry.by_id.get(puzzle_id) if puzzle_id else None
        session.current = puzzle

        if puzzle is None:
            # A hint counter without its puzzle would index another puzzle's
            # hint tuple, so it goes back to zero with the puzzle.
            session.hints_used = 0
        else:
            # The hint list may have been shortened since the save.
            session.hints_used = max(0, min(int(blob.get("hints_used", 0)), len(puzzle.hints)))

        session.prompted_rooms = set(blob.get("prompted_rooms", []))
        session.struggled = set(blob.get("struggled", []))

        # Unknown or absent mode falls back to the default rather than failing:
        # a hint preference is never worth refusing a save over.
        try:
            session.hint_mode = HintMode(blob.get("hint_mode", HintMode.STANDARD.value))
        except ValueError:
            session.hint_mode = HintMode.STANDARD

    def list_saves(self) -> str:
        """Format a human-readable listing of all save files."""
        try:
            files = sorted(p for p in self.save_root.iterdir() if p.suffix == ".json")
        except OSError as exc:
            return f"Error listing save files: {exc}"

        if not files:
            return "No save files found."

        rooms_by_id = {room.id: room for room in self.game.game_map.rooms.values()}
        lines = ["Available save files:"]
        for i, save_path in enumerate(files, start=1):
            try:
                data = json.loads(save_path.read_text())
                when = datetime.fromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                turns = data["turns"]
                location = rooms_by_id.get(data["player"]["location"])
                location_name = location.name if location else "?"
                lines.append(f"{i}. {save_path.stem} - {when} - Turn {turns} - {location_name}")
            except (OSError, json.JSONDecodeError, KeyError):
                lines.append(f"{i}. {save_path.stem} (metadata unavailable)")
        return "\n".join(lines)

    def delete_save(self, save_name: str) -> str:
        """Delete a save file by name."""
        path = self._save_path(save_name)
        if not path.exists():
            return f"Save file '{path.name}' not found."
        try:
            path.unlink()
        except OSError as exc:
            return f"Error deleting save file: {exc}"
        return f"Save file '{path.name}' deleted."
