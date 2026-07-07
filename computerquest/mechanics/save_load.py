# ABOUTME: Persistent save/load for game state. Ported from archive/saveload.py.
# ABOUTME: Step 1.2 removed the no-op stub; tk-24fa9f restores a real impl.

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from computerquest.config import SAVE_DIR

# Bump when the on-disk schema changes in a way old saves can't be read.
# 1.1 adds player.solved_puzzles / attempted_puzzles; 1.0 saves still load
# (the new fields default to empty).
SAVE_SCHEMA_VERSION = "1.1"
_COMPATIBLE_VERSIONS = frozenset({"1.0", SAVE_SCHEMA_VERSION})


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
        """Mutate self.game in place to match the deserialized state."""
        game = self.game
        game.turns = state["turns"]
        game_state = state["game_state"]
        game.game_over = game_state["game_over"]
        game.victory = game_state["victory"]
        game.all_viruses_found = game_state["all_viruses_found"]

        rooms_by_id = {room.id: room for room in game.game_map.rooms.values()}

        player_state = state["player"]
        location = rooms_by_id.get(player_state["location"])
        if location is None:
            raise KeyError(f"unknown location id {player_state['location']!r}")

        player = game.player
        player.location = location
        player.items = player_state["items"]
        player.health = player_state["health"]
        player.name = player_state["name"]
        player.found_viruses = player_state["found_viruses"]
        player.quarantined_viruses = player_state["quarantined_viruses"]
        player.knowledge = player_state["knowledge"]
        # Absent in 1.0 saves; default to empty rather than failing.
        player.solved_puzzles = set(player_state.get("solved_puzzles", []))
        player.attempted_puzzles = set(player_state.get("attempted_puzzles", []))
        # Knowledge is derived state since the microquiz cutover: rederive
        # from the solved set rather than trusting what the file stored.
        self.game._recompute_knowledge()

        for room_id, room_state in state["components"].items():
            room = rooms_by_id.get(room_id)
            if room is None:
                continue  # Saved component no longer exists in current world.
            room.items = room_state["items"]
            room.visited = room_state["visited"]
            if hasattr(room, "error_state"):
                room.error_state = room_state.get("error_state")
            if hasattr(room, "power_state"):
                room.power_state = room_state.get("power_state", "on")

        # Sync the map_grid visited markers with restored room state.
        for room_key, room in game.game_map.rooms.items():
            if room_key in game.map_grid and room.visited:
                game.map_grid[room_key]["visited"] = True

        if hasattr(game, "progress"):
            game.progress.update()

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
