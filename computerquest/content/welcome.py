# ABOUTME: The opening banner, mission briefing, status bar, and first room view.
# ABOUTME: Returns a string so both the CLI and the web server can render it.

from __future__ import annotations

from typing import Any

from computerquest.config import INVENTORY_LIMIT, VIRUS_TYPES
from computerquest.utils.helpers import Colors, format_look_output


def render_welcome(player: Any) -> str:
    """Build the welcome screen for `player`.

    The status bar reads live player state, so re-rendering mid-game shows
    current health, inventory, and virus counts rather than starting values.
    """
    total_viruses = len(VIRUS_TYPES)
    rule = "━" * 78

    lines = [
        rule,
        f"{Colors.CYAN}   █▄▀ █▀█ █▀▄ █▀▀ █▄▀ █   █▀█ █░█ █▀▄   █▀▀ █▀█ █▀▄▀█ █▀█ █░█ ▀█▀ █▀▀ █▀█   █▀█ █░█ █▀▀ █▀ ▀█▀{Colors.RESET}",
        f"{Colors.CYAN}   █░█ █▄█ █▄▀ ██▄ █░█ █▄▄ █▄█ █▄█ █▄▀   █▄▄ █▄█ █░▀░█ █▀▀ █▄█ ░█░ ██▄ █▀▄   ▀▀█ █▄█ ██▄ ▄█ ░█░{Colors.RESET}",
        rule,
        f"\n┏━━━━━━━━━━━━━━━━━━━━━━━━ {Colors.YELLOW}{Colors.BOLD}MISSION BRIEFING{Colors.RESET} ━━━━━━━━━━━━━━━━━━━━━━━━┓",
        "│                                                                    │",
        f"│  Welcome to the {Colors.CYAN}KodeKloud Computer Architecture Quest!{Colors.RESET}             │",
        "│                                                                    │",
        "│  You are a security program deployed into a computer system        │",
        f"│  infected with multiple {Colors.RED}viruses{Colors.RESET}. Your mission is to locate and     │",
        "│  quarantine all viruses while learning about computer architecture.│",
        "│                                                                    │",
        "│  As you travel through the system, from CPU to memory to storage   │",
        "│  and beyond, you'll discover how each component works and how      │",
        "│  they interconnect.                                                │",
        "│                                                                    │",
        "│  Good luck, Security Program! The system's integrity depends on you│",
        "│                                                                    │",
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
        "\n" + rule,
        f"  {Colors.BOLD}STATUS:{Colors.RESET} Health: {Colors.GREEN}{player.health}/{player.max_health}{Colors.RESET} | Items: {len(player.items)}/{INVENTORY_LIMIT} | Viruses: {Colors.GREEN}{len(player.found_viruses)}/{total_viruses} Found, {len(player.quarantined_viruses)}/{total_viruses} Quarantined{Colors.RESET}",
        rule,
        f"\n  {Colors.BOLD}CONTROLS:{Colors.RESET} Type '{Colors.GREEN}?{Colors.RESET}' for command help | '{Colors.GREEN}n/s/e/w{Colors.RESET}' to move | '{Colors.GREEN}l{Colors.RESET}' to look | '{Colors.GREEN}i{Colors.RESET}' for inventory",
        "\n"
        + format_look_output(
            player.location,
            player.location.doors,
            list(player.location.items.keys()),
            player=player,
        ),
    ]

    # Each entry was previously emitted by its own print(), which appends a
    # newline; joining and adding a trailing newline reproduces that exactly.
    return "\n".join(lines) + "\n"
