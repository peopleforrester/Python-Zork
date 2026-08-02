# ABOUTME: Derives "what should I do next" from live game state.
# ABOUTME: Narrows the search without naming a room an unfound virus is in.

from __future__ import annotations

import textwrap
from collections import Counter
from typing import Any

from computerquest.config import MAX_KNOWLEDGE, VIRUS_TYPES, is_virus_name

#: How many objectives to surface at once. The failure mode being avoided is a
#: wall of everything; the opposite failure is an empty screen, so a finished
#: game gets a closing line instead of nothing.
MAX_SHOWN = 4


def _unsolved_by_area(game: Any) -> dict[str, int]:
    """Count unsolved puzzles per subject area across the whole world."""
    counts: dict[str, int] = {}
    for room in game.game_map.rooms.values():
        for puzzle_id in room.puzzles:
            puzzle = game.puzzle_registry.by_id.get(puzzle_id)
            if puzzle is None or puzzle_id in game.player.solved_puzzles:
                continue
            counts[puzzle.subject_area] = counts.get(puzzle.subject_area, 0) + 1
    return counts


def _region_of(game: Any, room_id: str) -> str:
    """A coarse zone name for a room, used to point without pinpointing."""
    if room_id.startswith("core1") or room_id.startswith("core2") or room_id == "cpu_package":
        return "the CPU package"
    if room_id.startswith(("l2_", "l3_", "ram_", "memory_")) or room_id == "virtual_memory":
        return "the memory hierarchy"
    if room_id in {"ssd", "hdd", "sata_ports", "storage_controller"}:
        return "the storage subsystem"
    if room_id in {"network_interface", "ethernet", "usb_ports"}:
        return "the I/O and network edge"
    if room_id in {"pcie_x16", "pcie_x1_1", "pcie_x1_2", "pcie_controller", "gpu"}:
        return "the PCIe complex"
    return "the platform controller area"


def build_objectives(game: Any) -> list[str]:
    """The next few things worth doing, most immediate first.

    Everything is computed from live state (visited flags, found and
    quarantined viruses, solved puzzles, room puzzle bindings) rather than a
    hand-written list, which would drift from content the way the per-file
    canonical-answer comments did.
    """
    player = game.player
    rooms = game.game_map.rooms
    out: list[str] = []

    # 1. Viruses already located outrank everything: the player can act now.
    pending = [v for v in player.found_viruses if v not in player.quarantined_viruses]
    for virus in pending[:2]:
        where = next(
            (r.name for r in rooms.values() if virus in r.items), "somewhere you have been"
        )
        out.append(f"Quarantine {virus} (last seen in {where}).")

    # 2. A puzzle in this very room is the cheapest next step.
    here = player.location
    unsolved_here = [
        game.puzzle_registry.by_id[p].title
        for p in here.puzzles
        if p in game.puzzle_registry.by_id and p not in player.solved_puzzles
    ]
    if unsolved_here:
        out.append(f"Solve the puzzle here: {unsolved_here[0]} ('solve').")

    # 3. Point at unsearched territory by region, never by room. Naming the room
    #    would hand over the search that scanning is supposed to be.
    # Viruses are ordinary items and `take` accepts them without a scan, so the
    # player's own pack is a hiding place the room sweep never checked.
    carried = [
        i for i in player.items
        if is_virus_name(i) and i not in player.found_viruses
    ]
    for virus in carried[:2]:
        out.append(f"You are carrying {virus}. Scan your inventory and contain it.")

    unlocated = len(VIRUS_TYPES) - len(set(player.found_viruses))
    if unlocated > 0:
        unvisited = [rid for rid, room in rooms.items() if not room.visited]
        if unvisited:
            # Ranked by unexplored rooms, not alphabetically: sorting by name
            # meant three uppercase region names always won the slice, so the
            # region with the most ground left could never be mentioned.
            ranked = Counter(_region_of(game, rid) for rid in unvisited)
            regions = [name for name, _ in ranked.most_common(3)]
            out.append(
                f"{unlocated} of {len(VIRUS_TYPES)} viruses are still unlocated. "
                f"Unexplored: {', '.join(regions)}. Use 'scan' as you go."
            )
        else:
            hidden = [
                r.name for r in rooms.values()
                if any(is_virus_name(i) and i not in player.found_viruses for i in r.items)
            ]
            if hidden:
                out.append(
                    f"{unlocated} of {len(VIRUS_TYPES)} still unlocated, and you have "
                    "walked every component. Re-scan the rooms you passed through."
                )

    # 4. Study where the meter is thinnest, so the suggestion is earned.
    unsolved = _unsolved_by_area(game)
    if unsolved:
        area = min(unsolved, key=lambda a: (player.knowledge.get(a, 0), a))
        level = player.knowledge.get(area, 0)
        # Every area maxes out well before its puzzles run out, so "weakest"
        # would otherwise be printed next to a full meter.
        if level >= MAX_KNOWLEDGE:
            out.append(
                f"Every meter is full; {sum(unsolved.values())} puzzles remain "
                "for their own sake."
            )
        else:
            out.append(
                f"Your weakest area is {area} ({level}/{MAX_KNOWLEDGE}); "
                f"{unsolved[area]} {area} puzzles remain."
            )

    return out[:MAX_SHOWN]


#: Objectives are variable-length, so this panel uses rules rather than a
#: bordered box: a fixed-width box cannot align around text it does not control.
_WIDTH = 70


def render_objectives(game: Any) -> str:
    """Player-facing objectives panel."""
    items = build_objectives(game)
    title = " OBJECTIVES "
    pad = max(0, _WIDTH - len(title))
    header = "━" * (pad // 2) + title + "━" * (pad - pad // 2)
    footer = "━" * _WIDTH

    if not items:
        # Emptiness alone is not completion: a virus in the pack produced no
        # objectives while the game was still unwinnable.
        won = len(game.player.quarantined_viruses) == len(VIRUS_TYPES)
        body = (
            "  The system is clean and every puzzle is solved. Nothing left to do."
            if won
            else "  No suggestions right now. Try 'scan' here, or 'status' for progress."
        )
        return f"{header}\n{body}\n{footer}"

    lines = []
    for item in items:
        wrapped = textwrap.wrap(item, width=_WIDTH - 4) or [item]
        lines.append(f"  - {wrapped[0]}")
        lines.extend(f"    {rest}" for rest in wrapped[1:])
    return header + "\n" + "\n".join(lines) + "\n" + footer
