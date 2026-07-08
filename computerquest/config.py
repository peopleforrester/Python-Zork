"""
KodeKloud Computer Quest Configuration

Central configuration file for game settings and constants
"""

from computerquest import __version__

# Game Information
GAME_NAME = "KodeKloud Computer Quest"
GAME_VERSION = __version__

# File System
SAVE_DIR = ".kodekloud_quest"

# Direction Constants
DIRECTION_MAPPING = {
    'north': 'n', 'n': 'n',
    'south': 's', 's': 's',
    'east': 'e', 'e': 'e',
    'west': 'w', 'w': 'w',
    'northeast': 'ne', 'ne': 'ne',
    'northwest': 'nw', 'nw': 'nw',
    'southeast': 'se', 'se': 'se',
    'southwest': 'sw', 'sw': 'sw',
    'up': 'u', 'u': 'u',
    'down': 'd', 'd': 'd'
}

DIRECTION_NAMES = {
    'n': 'North',
    's': 'South',
    'e': 'East',
    'w': 'West',
    'ne': 'Northeast',
    'nw': 'Northwest',
    'se': 'Southeast',
    'sw': 'Southwest',
    'u': 'Up',
    'd': 'Down'
}

# Virus Types
VIRUS_TYPES = [
    "boot_sector_virus",
    "rootkit_virus",
    "memory_resident_virus",
    "firmware_virus",
    "packet_sniffer_virus"
]

# Membership check used in place of substring matching ('virus' in name.lower())
# — the substring matcher false-positived on test fixtures named virus_item,
# and would not have been localizable. The canonical set lives here so new
# virus types only need one update.
_VIRUS_TYPE_SET = frozenset(VIRUS_TYPES)


def is_virus_name(name: str) -> bool:
    """True iff `name` matches a canonical virus identifier in VIRUS_TYPES."""
    return name in _VIRUS_TYPE_SET

# Component Knowledge Areas
KNOWLEDGE_AREAS = {
    "cpu": "CPU Architecture",
    "memory": "Memory Systems",
    "storage": "Storage Technologies",
    "networking": "Computer Networks",
    "security": "Security Concepts"
}

# Maximum knowledge level per area
MAX_KNOWLEDGE = 5

# Map display settings
MAP_WIDTH = 70
MAP_HEIGHT = 60

# Performance settings
PERFORMANCE_METRICS = ["speed", "capacity", "reliability"]

# Player limits (single source of truth for the cap and the health bar)
INVENTORY_LIMIT = 8
MAX_HEALTH = 20

# Feature flags
# Minigames (CPU pipeline, memory hierarchy) are simulator-backed and live
# as of the microquiz step-7 cutover; both delegate to mechanics.simulators.
ENABLE_MINIGAMES = True
