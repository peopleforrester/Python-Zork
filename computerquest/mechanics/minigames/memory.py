# ABOUTME: Memory hierarchy minigame; delegates hit/miss to simulators.cache.
# ABOUTME: The player steps an access pattern and watches locality play out.

from __future__ import annotations

from typing import Any

from computerquest.mechanics.minigames._common import Mode
from computerquest.mechanics.minigames.memory_patterns import (
    CACHE_CONFIG,
    PATTERN_BLURB,
    PATTERNS,
)
from computerquest.mechanics.simulators.cache import CacheSimulator

# Latency each level adds, for the educational pyramid display only. The
# interactive hit/miss decision is entirely the cache simulator's.
_PYRAMID = [
    ("Registers", "~0 cycles"),
    ("L1 cache", "~4 cycles"),
    ("L2 cache", "~12 cycles"),
    ("L3 cache", "~40 cycles"),
    ("RAM", "~200 cycles"),
    ("SSD", "~100k cycles"),
]

_TUNING_KNOWLEDGE = 4


class MemoryHierarchyMinigame:
    """Steps a canned access pattern through a single cache, one access at a
    time, asking CacheSimulator for the verdict on the trace so far. The
    minigame holds no cache state of its own."""

    def __init__(self, game: Any) -> None:
        self.game = game
        self.config: dict[str, Any] = dict(CACHE_CONFIG)
        self.pattern_name = "sequential"
        self.accesses = list(PATTERNS[self.pattern_name])
        self.cursor = 0
        self.hits = 0
        self.misses = 0
        self.mode = Mode.RUNNING
        self._sim = CacheSimulator()

    # --- state ------------------------------------------------------------

    def is_finished(self) -> bool:
        return self.mode is Mode.FINISHED

    def hit_rate(self) -> float:
        done = self.hits + self.misses
        return (self.hits / done) if done else 0.0

    def _verdict_at(self, index: int) -> str:
        """Hit or miss for access `index`, from the simulator's run over the
        trace up to and including it. O(n) per step, trivial for these sizes."""
        result = self._sim.run({**self.config, "accesses": self.accesses[: index + 1]})
        return result[index]

    # --- verbs ------------------------------------------------------------

    def set_pattern(self, name: str) -> str:
        if name not in PATTERNS:
            return f"Unknown pattern {name!r}. Try: {', '.join(PATTERNS)}."
        self.pattern_name = name
        self.accesses = list(PATTERNS[name])
        self.reset()
        return f"Pattern set to '{name}' ({PATTERN_BLURB[name]}).\n\n" + self.explain()

    def set_cache_size(self, size: int) -> str:
        if self.game.player.knowledge.get("memory", 0) < _TUNING_KNOWLEDGE:
            return (
                "You need deeper memory knowledge (level 4) to retune the cache. "
                "Solve more memory puzzles first."
            )
        assoc = int(self.config["associativity"])
        if size < 1 or size % assoc != 0:
            return f"Cache size must be a positive multiple of {assoc}."
        self.config["size_lines"] = size
        self.reset()
        return f"L1 cache resized to {size} lines.\n\n" + self.explain()

    def step(self) -> str:
        if self.mode is Mode.FINISHED:
            return "Pattern exhausted. Use 'simulate reset' or 'simulate pattern <name>'."
        verdict = self._verdict_at(self.cursor)
        addr = self.accesses[self.cursor]
        line = addr // int(self.config["line_size_bytes"])
        if verdict == "H":
            self.hits += 1
            note = f"HIT  addr 0x{addr:03X} (line {line}) already cached"
        else:
            self.misses += 1
            note = f"MISS addr 0x{addr:03X} (line {line}) fetched from RAM"
        self.cursor += 1
        if self.cursor >= len(self.accesses):
            self.mode = Mode.FINISHED
            return note + "\n\n" + self._debrief()
        return f"{note}\n{self._progress()}"

    def reset(self) -> str:
        self.cursor = 0
        self.hits = 0
        self.misses = 0
        self.mode = Mode.RUNNING
        return f"Reset '{self.pattern_name}' to the first access."

    # --- rendering --------------------------------------------------------

    def explain(self) -> str:
        lines = ["MEMORY HIERARCHY SIMULATION", ""]
        for name, latency in _PYRAMID:
            lines.append(f"  {name:<10} {latency}")
        lines.append("")
        lines.append(
            f"Interactive cache: {self.config['size_lines']} lines, "
            f"{self.config['line_size_bytes']}-byte lines, "
            f"{self.config['associativity']}-way, {self.config['policy']}."
        )
        lines.append(f"Pattern: '{self.pattern_name}' ({PATTERN_BLURB[self.pattern_name]}).")
        lines.append(f"Accesses: {len(self.accesses)}")
        lines.append("")
        lines.append("Use 'simulate step' to issue the next access,")
        lines.append("'simulate pattern <sequential|loop|stride|random>' to switch,")
        lines.append("'simulate cache l1 <size>' to retune (needs memory level 4),")
        lines.append("'simulate stop' to leave.")
        return "\n".join(lines)

    def get_status(self) -> str:
        if self.mode is Mode.FINISHED:
            return self._debrief()
        return self._progress()

    def _progress(self) -> str:
        return (
            f"Access {self.cursor}/{len(self.accesses)}  "
            f"hits {self.hits}  misses {self.misses}  "
            f"hit rate {self.hit_rate() * 100:.0f}%"
        )

    def _debrief(self) -> str:
        total = self.hits + self.misses
        return "\n".join(
            [
                "DEBRIEF",
                f"  Pattern: '{self.pattern_name}' ({PATTERN_BLURB[self.pattern_name]})",
                f"  Accesses: {total}  Hits: {self.hits}  Misses: {self.misses}",
                f"  Hit rate: {self.hit_rate() * 100:.0f}%",
                "  Switch patterns to compare how locality drives the hit rate.",
            ]
        )
