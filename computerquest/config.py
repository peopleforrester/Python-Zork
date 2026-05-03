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

# Feature flags
# Minigames (CPU pipeline, memory hierarchy) ship as placeholder stubs.
# Step 4.1 (tk-a7098e) flips this to True once real implementations land.
ENABLE_MINIGAMES = False
