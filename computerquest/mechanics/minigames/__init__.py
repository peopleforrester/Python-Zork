# ABOUTME: Minigames subpackage; simulator-backed CPU pipeline and memory games.
# ABOUTME: Public API re-exporting the two playable minigame classes.

from computerquest.mechanics.minigames.cpu import CPUPipelineMinigame
from computerquest.mechanics.minigames.memory import MemoryHierarchyMinigame

__all__ = ["CPUPipelineMinigame", "MemoryHierarchyMinigame"]
