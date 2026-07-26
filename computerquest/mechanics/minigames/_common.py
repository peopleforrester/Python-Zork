# ABOUTME: Shared run-mode enum for the minigames.
# ABOUTME: Keeps cpu.py and memory.py agreeing on the running/finished states.

from __future__ import annotations

from enum import Enum


class Mode(Enum):
    RUNNING = "running"
    FINISHED = "finished"
