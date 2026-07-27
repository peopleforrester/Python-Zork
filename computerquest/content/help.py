# ABOUTME: The full `help` command screen. Hand-aligned box art, so edit the
# ABOUTME: padding as carefully as the words; tests pin the output byte-exactly.

from __future__ import annotations

from computerquest.utils.helpers import Colors


def help_text() -> str:
    """Render the full command reference.

    Colors resolve to empty strings when stdout is not a TTY, so the box art
    still aligns in captured output.
    """
    return f"""┏━━━━━━━━━━━━━━━━━━ {Colors.YELLOW}{Colors.BOLD}KODEKLOUD COMPUTER QUEST COMMANDS{Colors.RESET} ━━━━━━━━━━━━━━━━━━┓
│                                                                          │
│  {Colors.BOLD}Movement:{Colors.RESET}                                                               │
│    go [direction]   - Move between components (n, s, e, w, ne, sw, etc.) │
│    [direction]      - You can also just type the direction (n, s, e, w)  │
│                                                                          │
│  {Colors.BOLD}Exploration:{Colors.RESET}                                                            │
│    {Colors.GREEN}look, l{Colors.RESET}          - Examine your current location                      │
│    {Colors.GREEN}look [item]{Colors.RESET}      - Examine a specific item                            │
│    {Colors.GREEN}read [item], r{Colors.RESET}   - Read text content of an item                       │
│    {Colors.GREEN}map, m{Colors.RESET}           - Display a map of visited computer components       │
│    {Colors.GREEN}motherboard, mb{Colors.RESET}  - Show the motherboard layout of the computer system │
│                                                                          │
│  {Colors.BOLD}Inventory:{Colors.RESET}                                                              │
│    {Colors.GREEN}inventory, i{Colors.RESET}     - List items in your storage                         │
│    {Colors.GREEN}take [item], t{Colors.RESET}   - Add an item to your inventory                      │
│    {Colors.GREEN}drop [item]{Colors.RESET}      - Remove an item from your inventory                 │
│                                                                          │
│  {Colors.BOLD}Security Functions:{Colors.RESET}                                                     │
│    {Colors.GREEN}scan, sc{Colors.RESET}         - Search for viruses in current location             │
│    {Colors.GREEN}scan [item]{Colors.RESET}      - Check if a specific item contains a virus          │
│    {Colors.GREEN}advscan{Colors.RESET}          - Perform advanced scan (requires decoder_tool)      │
│    {Colors.GREEN}advscan [item]{Colors.RESET}   - Perform advanced scan on specific item             │
│    {Colors.GREEN}analyze [item]{Colors.RESET}   - Deeply analyze an item for hidden properties       │
│    {Colors.GREEN}quarantine [virus]{Colors.RESET} - Contain a discovered virus                       │
│                                                                          │
│  {Colors.BOLD}Puzzles:{Colors.RESET}                                                                │
│    {Colors.GREEN}solve [id]{Colors.RESET}       - Start a puzzle in this room (or list them)         │
│    {Colors.GREEN}answer [tokens]{Colors.RESET}  - Commit your prediction for the active puzzle       │
│    {Colors.GREEN}hint{Colors.RESET}             - Next hint (the first one is free)                  │
│    {Colors.GREEN}skip{Colors.RESET}             - Put the active puzzle aside                        │
│                                                                          │
│  {Colors.BOLD}Information:{Colors.RESET}                                                            │
│    {Colors.GREEN}status{Colors.RESET}           - Check your virus discovery progress                │
│    {Colors.GREEN}knowledge{Colors.RESET}        - View your computer architecture knowledge          │
│    {Colors.GREEN}about [topic]{Colors.RESET}    - Get information about a computer component         │
│                                                                          │
│  {Colors.BOLD}Progress Tracking:{Colors.RESET}                                                      │
│    {Colors.GREEN}achievements{Colors.RESET}     - View your achievements and progress report         │
│    {Colors.GREEN}stats{Colors.RESET}            - Alternative command for achievements               │
│                                                                          │
│  {Colors.BOLD}Educational Features:{Colors.RESET}                                                   │
│    {Colors.GREEN}visualize [comp]{Colors.RESET} - Show visualization of a component                  │
│    {Colors.GREEN}viz [comp]{Colors.RESET}       - Shorthand for visualize                            │
│    {Colors.GREEN}simulate cpu{Colors.RESET}     - Start CPU pipeline simulation minigame             │
│    {Colors.GREEN}simulate memory{Colors.RESET}  - Start memory hierarchy simulation                  │
│    {Colors.GREEN}simulate step{Colors.RESET}    - Advance simulation by one step                     │
│    {Colors.GREEN}simulate forward{Colors.RESET} - (CPU) toggle result forwarding on/off              │
│    {Colors.GREEN}simulate pattern{Colors.RESET} - (memory) sequential|loop|stride|random             │
│    {Colors.GREEN}simulate toggle{Colors.RESET}  - Toggle between simulation modes                    │
│    {Colors.GREEN}simulate reset{Colors.RESET}   - Reset the simulation                               │
│                                                                          │
│  {Colors.BOLD}Save/Load:{Colors.RESET}                                                              │
│    {Colors.GREEN}save [name]{Colors.RESET}      - Save your game progress (optional name)            │
│    {Colors.GREEN}load [name]{Colors.RESET}      - Load a saved game                                  │
│    {Colors.GREEN}saves{Colors.RESET}            - List all available save files                      │
│    {Colors.GREEN}deletesave [name]{Colors.RESET} - Delete a saved game                               │
│                                                                          │
│  {Colors.BOLD}System:{Colors.RESET}                                                                 │
│    {Colors.GREEN}help, h{Colors.RESET}          - Show this help message                             │
│    {Colors.GREEN}?{Colors.RESET}                - Show quick help overlay                            │
│    {Colors.GREEN}clear, cls, c{Colors.RESET}    - Clear the screen and refresh display               │
│    {Colors.GREEN}quit, q, exit{Colors.RESET}    - Exit the game                                      │
│                                                                          │
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

{Colors.BOLD}Main Shortcuts:{Colors.RESET}
  Movement: {Colors.GREEN}[N]{Colors.RESET}orth {Colors.GREEN}[S]{Colors.RESET}outh {Colors.GREEN}[E]{Colors.RESET}ast {Colors.GREEN}[W]{Colors.RESET}est {Colors.GREEN}[NE]{Colors.RESET} {Colors.GREEN}[SE]{Colors.RESET} {Colors.GREEN}[SW]{Colors.RESET} {Colors.GREEN}[NW]{Colors.RESET} {Colors.CYAN}[U]{Colors.RESET}p {Colors.CYAN}[D]{Colors.RESET}own
  Commands: {Colors.GREEN}[L]{Colors.RESET}ook {Colors.GREEN}[I]{Colors.RESET}nventory {Colors.GREEN}[T]{Colors.RESET}ake {Colors.GREEN}[H]{Colors.RESET}elp {Colors.GREEN}[M]{Colors.RESET}ap {Colors.GREEN}[C]{Colors.RESET}lear {Colors.GREEN}[Q]{Colors.RESET}uit {Colors.GREEN}[Sc]{Colors.RESET}an

Use '{Colors.GREEN}?{Colors.RESET}' for a quick command reference at any time.
"""
