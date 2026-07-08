# ABOUTME: Canned access patterns for the memory hierarchy minigame.
# ABOUTME: Each is a deterministic byte-address list; the cache simulator grades it.

# The minigame's cache: 4 lines, fully-associative, 64-byte lines, LRU. Hit
# counts below are the CacheSimulator's output for this config and are pinned
# by tests, so the four patterns stay pedagogically distinct:
#   loop 15/18 (83%) > sequential 12/16 (75%) > random 3/12 (25%) > stride 0/12.
CACHE_CONFIG = {
    "policy": "LRU",
    "size_lines": 4,
    "line_size_bytes": 64,
    "associativity": 4,
}

PATTERNS: dict[str, list[int]] = {
    # Spatial locality: four bytes within each of four lines. One cold miss
    # per line, then three hits inside it.
    "sequential": [line * 64 + off for line in range(4) for off in (0, 16, 32, 48)],
    # Temporal locality: a 3-line working set that fits the 4-line cache,
    # revisited six times. Misses only on the first pass.
    "loop": [0, 64, 128] * 6,
    # Stride larger than a line: every access is a fresh line, so spatial
    # prefetch buys nothing and every access misses.
    "stride": [i * 128 for i in range(12)],
    # Thrashing: six distinct lines (more than the cache holds) in a scrambled
    # order with a few quick reuses, so a handful of accidental hits survive.
    "random": [0, 64, 0, 320, 384, 64, 192, 448, 192, 256, 0, 384],
}

PATTERN_BLURB: dict[str, str] = {
    "sequential": "walks addresses within each line (spatial locality)",
    "loop": "revisits a small working set (temporal locality)",
    "stride": "jumps a full line every access (defeats spatial locality)",
    "random": "scatters across more lines than fit (thrashing)",
}
