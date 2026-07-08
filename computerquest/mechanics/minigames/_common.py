# ABOUTME: Shared bits for the minigames: run mode and a box-drawing helper.
# ABOUTME: Keeps cpu.py and memory.py free of duplicated rendering scaffolding.

from __future__ import annotations

from enum import Enum


class Mode(Enum):
    RUNNING = "running"
    FINISHED = "finished"


def boxed(title: str, body: str) -> str:
    """Wrap body text in a titled box matching the game's other panels."""
    width = 58
    top = f"┏━━ {title} " + "━" * max(0, width - len(title) - 5) + "┓"
    bottom = "┗" + "━" * (width) + "┛"
    return f"{top}\n{body}\n{bottom}"
