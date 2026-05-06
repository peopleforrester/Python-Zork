"""
Helper utilities for KodeKloud Computer Quest
"""

import textwrap

from computerquest.config import DIRECTION_NAMES


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    REVERSED = "\033[7m"


def prefix_match(prefix, candidates):
    """
    Match a prefix with candidates, return the full string if unique match is found

    Args:
        prefix (str): The prefix to match
        candidates (list): List of possible matches

    Returns:
        str: The full match if unique, otherwise the original prefix
    """
    if len(prefix) < 2:
        return prefix  # Don't try to match single-letter prefixes

    # Check for exact match first
    if prefix in candidates:
        return prefix

    # Check for prefix match
    matches = [item for item in candidates if item.startswith(prefix)]

    # Return the matched item if only one match, otherwise return original
    if len(matches) == 1:
        return matches[0]
    else:
        return prefix


def format_box(title, content, width=70):
    """
    Create a nicely formatted text box

    Args:
        title (str): Title for the box
        content (str): Content to display in the box
        width (int): Width of the box

    Returns:
        str: Formatted text box
    """
    result = "+" + "-" * width + "+\n"
    result += "|" + title.center(width) + "|\n"
    result += "+" + "-" * width + "+\n"

    for line in content.split("\n"):
        result += "| " + line.ljust(width - 1) + "|\n"

    result += "+" + "-" * width + "+"
    return result


def format_fancy_box(title, content, width=70, border_char="━"):
    """
    Create a fancy formatted text box with unicode characters

    Args:
        title (str): Title for the box
        content (str): Content to display in the box
        width (int): Width of the box
        border_char (str): Character to use for borders

    Returns:
        str: Formatted fancy text box
    """
    result = "┏" + border_char * (width - 2) + "┓\n"
    result += "┃ " + title.ljust(width - 4) + " ┃\n"
    result += "┗" + border_char * (width - 2) + "┛\n"

    # Process content lines
    for line in content.split("\n"):
        result += "  " + line + "\n"

    return result


def truncate_desc(desc, max_length=50):
    """
    Truncate description to a reasonable length

    Args:
        desc (str): Description to truncate
        max_length (int): Maximum length

    Returns:
        str: Truncated description
    """
    if not desc:
        return ""

    # Get first sentence or use whole string
    short_desc = desc.split(".")[0] if "." in desc else desc

    # Truncate if too long
    if len(short_desc) > max_length:
        short_desc = short_desc[: max_length - 3] + "..."

    return short_desc


def format_list(items, prefix="- "):
    """
    Format a list of items with prefixes

    Args:
        items (list): List of items to format
        prefix (str): Prefix for each line

    Returns:
        str: Formatted list as string
    """
    if not items:
        return ""

    return "\n".join(f"{prefix}{item}" for item in items)


def format_look_output(location, connections, items, technical_details=None, player=None):
    """
    Format the look command output for better readability.

    Args:
        location: Component object with name and description
        connections: Dictionary of directions and connected components
        items: Dictionary of items in the location
        technical_details: Optional list of technical details to display
        player: Optional Player; when provided, the status bar reflects real
            health and inventory size instead of placeholder defaults.

    Returns:
        str: Formatted look output
    """
    output = []
    available_directions = connections.keys()

    # Location header with highlight for current location
    output.append("┏" + "━" * 20 + " LOCATION " + "━" * 20 + "┓")
    output.append(f"  {Colors.YELLOW}{Colors.BOLD}{location.name}{Colors.RESET}")
    output.append("┗" + "━" * 51 + "┛\n")

    # Description
    output.append(f"{Colors.BOLD}Description:{Colors.RESET}")
    description_lines = textwrap.wrap(location.desc, width=70)
    output.extend([f"  {line}" for line in description_lines])
    output.append("")

    # Connections with color-coded directions
    output.append("┏" + "━" * 18 + " AVAILABLE CONNECTIONS " + "━" * 18 + "┓")

    # Format regular connections with color coding
    reg_connections = []
    for direction, connected_room in connections.items():
        dir_name = DIRECTION_NAMES.get(direction, direction).upper()

        # Color code the direction
        colored_dir = (
            f"{Colors.GREEN}[{dir_name[0]}]{dir_name[1:]}{Colors.RESET}"
            if len(dir_name) > 1
            else f"{Colors.GREEN}[{dir_name}]orth{Colors.RESET}"
        )

        if len(dir_name) == 1:
            reg_connections.append(f"{colored_dir}: {connected_room.name}")
        elif len(dir_name) == 2:
            reg_connections.append(
                f"{Colors.GREEN}[{dir_name}]{Colors.RESET}: {connected_room.name}"
            )
        else:
            reg_connections.append(f"{colored_dir}: {connected_room.name}")

    # Split into lines of 2-3 connections each
    conn_lines = []
    for i in range(0, len(reg_connections), 3):
        conn_lines.append("  " + "  ".join(reg_connections[i : i + 3]))

    output.extend(conn_lines)
    output.append("┗" + "━" * 60 + "┛\n")

    # Create a mapping of direction codes to compass positions
    direction_map = {
        "n": (0, 2),  # North
        "s": (4, 2),  # South
        "e": (2, 4),  # East
        "w": (2, 0),  # West
        "ne": (1, 3),  # Northeast
        "nw": (1, 1),  # Northwest
        "se": (3, 3),  # Southeast
        "sw": (3, 1),  # Southwest
        "u": None,  # Up (will be handled separately)
        "d": None,  # Down (will be handled separately)
    }

    # Create the compass with arrows for available paths
    compass = ["      N      ", "    NW NE    ", "   W  +  E   ", "    SW SE    ", "      S      "]

    # Convert to list of lists for easier manipulation
    compass_grid = [list(line) for line in compass]

    # Get all possible directions for showing blockers
    all_directions = ["n", "s", "e", "w", "ne", "nw", "se", "sw"]

    # First, mark unavailable directions with blockers
    for direction in all_directions:
        if (
            direction not in available_directions
            and direction in direction_map
            and direction_map[direction]
        ):
            row, col = direction_map[direction]
            compass_grid[row][col] = "█"  # Blocker for unavailable direction

    # Then add arrows for available directions
    for direction in available_directions:
        if direction in direction_map and direction_map[direction]:
            row, col = direction_map[direction]
            # Replace with colored arrow
            if direction == "n":
                compass_grid[row][col] = f"{Colors.GREEN}↑{Colors.RESET}"
            elif direction == "s":
                compass_grid[row][col] = f"{Colors.GREEN}↓{Colors.RESET}"
            elif direction == "e":
                compass_grid[row][col] = f"{Colors.GREEN}→{Colors.RESET}"
            elif direction == "w":
                compass_grid[row][col] = f"{Colors.GREEN}←{Colors.RESET}"
            elif direction == "ne":
                compass_grid[row][col] = f"{Colors.GREEN}↗{Colors.RESET}"
            elif direction == "nw":
                compass_grid[row][col] = f"{Colors.GREEN}↖{Colors.RESET}"
            elif direction == "se":
                compass_grid[row][col] = f"{Colors.GREEN}↘{Colors.RESET}"
            elif direction == "sw":
                compass_grid[row][col] = f"{Colors.GREEN}↙{Colors.RESET}"

    # Convert back to strings but keep color codes
    enhanced_compass = ["".join(row) for row in compass_grid]

    # Add up/down indicators if available with color coding
    up_down_indicators = []
    if "u" in available_directions:
        up_down_indicators.append(f"{Colors.CYAN}[U]p{Colors.RESET}: {connections['u'].name}")
    if "d" in available_directions:
        up_down_indicators.append(f"{Colors.CYAN}[D]own{Colors.RESET}: {connections['d'].name}")

    # Add directional compass with improved formatting
    if len(connections) > 0:
        output.append(f"  {Colors.BOLD}Directional Compass:{Colors.RESET}")
        for line in enhanced_compass:
            output.append(f"  {line}")

        if up_down_indicators:
            output.append("  " + "  ".join(up_down_indicators))

    # Add breadcrumb path display with highlighting
    if hasattr(location, "parent") and location.parent:
        path_parts = []
        current = location
        while hasattr(current, "parent") and current.parent:
            path_parts.insert(0, current.parent.name)
            current = current.parent

        if path_parts:
            # Format the breadcrumb with color highlighting for the current location
            breadcrumb_parts = [f"{part}" for part in path_parts]
            breadcrumb_parts.append(f"{Colors.YELLOW}{location.name}{Colors.RESET}")
            breadcrumb = f" {Colors.BLUE}→{Colors.RESET} ".join(breadcrumb_parts)
            output.append(f"\n{Colors.BOLD}Location Path:{Colors.RESET} {breadcrumb}")

    # Components with highlighting
    if items:
        output.append("\n┏" + "━" * 20 + " COMPONENTS " + "━" * 20 + "┓")
        for item in items:
            output.append(f"  • {Colors.CYAN}{item}{Colors.RESET}")
        output.append("┗" + "━" * 51 + "┛")
        output.append(
            f"\nType '{Colors.GREEN}examine{Colors.RESET} [component]' or '{Colors.GREEN}take{Colors.RESET} [component]' to interact.\n"
        )

    # Technical details if visited
    if technical_details:
        output.append("┏" + "━" * 19 + " TECHNICAL DETAILS " + "━" * 19 + "┓")
        for line in technical_details:
            output.append(f"  {line}")
        output.append("┗" + "━" * 51 + "┛")

    # Enhanced status bar with real game state from player.
    from computerquest.config import INVENTORY_LIMIT, MAX_HEALTH, VIRUS_TYPES

    total_viruses = len(VIRUS_TYPES)

    if player is not None:
        max_health = player.max_health
        current_health = player.health
        inventory_size = len(player.items)
        found_viruses = len(player.found_viruses)
        quar_viruses = len(player.quarantined_viruses)
    else:
        # Pre-game / no-player surfaces fall back to a full-health, empty bag
        # snapshot rather than feeding stale or fabricated state.
        max_health = MAX_HEALTH
        current_health = MAX_HEALTH
        inventory_size = len(items) if items else 0
        found_viruses = 0
        quar_viruses = 0

    # Set color based on health percentage
    health_percent = current_health / max_health if max_health else 0
    if health_percent > 0.7:
        health_color = Colors.GREEN
    elif health_percent > 0.3:
        health_color = Colors.YELLOW
    else:
        health_color = Colors.RED

    virus_color = Colors.RED if found_viruses > quar_viruses else Colors.GREEN

    # Create a compact status bar with more game state information
    output.append("\n" + "━" * 70)
    output.append(
        f"  {Colors.BOLD}STATUS:{Colors.RESET} Health: {health_color}{current_health}/{max_health}{Colors.RESET} | Items: {inventory_size}/{INVENTORY_LIMIT} | Viruses: {virus_color}{found_viruses}/{total_viruses} Found, {quar_viruses}/{total_viruses} Quarantined{Colors.RESET}"
    )

    # Add system location info to status bar
    if hasattr(location, "category"):
        category = location.category.capitalize() if hasattr(location, "category") else "System"
        output.append(
            f"  {Colors.BOLD}SYSTEM:{Colors.RESET} {category} Component | Type '{Colors.GREEN}?{Colors.RESET}' for command help | '{Colors.GREEN}m{Colors.RESET}' for map"
        )
    else:
        output.append(
            f"  {Colors.BOLD}SYSTEM:{Colors.RESET} Computer Component | Type '{Colors.GREEN}?{Colors.RESET}' for command help | '{Colors.GREEN}m{Colors.RESET}' for map"
        )

    output.append("━" * 70)

    return "\n".join(output)
