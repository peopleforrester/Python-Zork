"""
Command Pattern implementation

Handles command processing through the Command pattern.
"""

from computerquest.config import VIRUS_TYPES


class Command:
    """Base class for all commands"""
    def __init__(self, game, args=None):
        self.game = game
        self.args = args or []

    def execute(self):
        """Execute the command - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute()")

    def can_execute(self):
        """Check if command can be executed - optional validation"""
        return True, None

class MoveCommand(Command):
    """Command to move player between components"""
    def can_execute(self):
        if not self.args:
            return False, "Please specify a direction."
        return True, None

    def execute(self):
        direction = self.args[0].lower()
        return self.game.move(direction)

class LookCommand(Command):
    """Command to look around or examine an item"""
    def execute(self):
        if not self.args:
            # Mark component as visited to reveal more technical details
            self.game.player.location.mark_visited()
            return self.game.player.look()
        else:
            item_name = self.args[0].lower()

            # Try to match item prefix
            if item_name not in self.game.player.location.items and item_name not in self.game.player.items:
                room_match = self.game._match_item_prefix(item_name)
                inv_match = self.game._match_inventory_item_prefix(item_name)

                # Use the best match found
                if room_match in self.game.player.location.items:
                    item_name = room_match
                elif inv_match in self.game.player.items:
                    item_name = inv_match

            return self.game.player.look(item_name)

class TakeCommand(Command):
    """Command to take an item"""
    def can_execute(self):
        if not self.args:
            return False, "What do you want to take?"
        return True, None

    def execute(self):
        item_name = self.args[0].lower()
        # Match item prefix
        item_name = self.game._match_item_prefix(item_name)
        result = self.game.player.take(item_name)
        self.game.turns += 1
        return result

class DropCommand(Command):
    """Command to drop an item"""
    def can_execute(self):
        if not self.args:
            return False, "What do you want to drop?"
        item_name = self.game._match_inventory_item_prefix(self.args[0].lower())
        if item_name not in self.game.player.items:
            return False, f"You don't have a {self.args[0]}."
        return True, None

    def execute(self):
        item_name = self.game._match_inventory_item_prefix(self.args[0].lower())
        result = self.game.player.drop(item_name)
        self.game.turns += 1
        return result

class InventoryCommand(Command):
    """Command to show player's inventory"""
    def execute(self):
        if not self.game.player.items:
            return "┏━━━━━━━━━━━━━━━ SYSTEM STORAGE ━━━━━━━━━━━━━━━┓\n  Your system storage is empty.\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

        result = "┏━━━━━━━━━━━━━━━ SYSTEM STORAGE ━━━━━━━━━━━━━━━┓\n"
        for item, desc in self.game.player.items.items():
            # Show abbreviated description for inventory listing
            short_desc = desc.split('.')[0] if '.' in desc else desc
            if len(short_desc) > 50:
                short_desc = short_desc[:47] + "..."
            result += f"  • {item}: {short_desc}\n"
        result += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
        return result

class ScanCommand(Command):
    """Command to scan for viruses"""
    def execute(self):
        if not self.args:
            result = self.game.player.scan()
            # Check for game winning conditions
            if len(self.game.player.found_viruses) == len(VIRUS_TYPES):
                self.game.all_viruses_found = True
        else:
            target = self.args[0].lower()
            result = self.game.player.scan(target)

        self.game.turns += 1
        return result

class AdvancedScanCommand(Command):
    """Command to perform advanced scan"""
    def execute(self):
        if not self.args:
            result = self.game.player.advanced_scan()
            # Check for game winning conditions
            if len(self.game.player.found_viruses) == len(VIRUS_TYPES):
                self.game.all_viruses_found = True
        else:
            target = self.args[0].lower()
            result = self.game.player.advanced_scan(target)

        self.game.turns += 1
        return result

class AnalyzeCommand(Command):
    """Command to deeply analyze an item"""
    def can_execute(self):
        if not self.args:
            return False, "What do you want to analyze? Usage: analyze [item]"
        return True, None

    def execute(self):
        target = self.args[0].lower()
        result = self.game.player.analyze(target)
        self.game.turns += 1
        return result

class QuarantineCommand(Command):
    """Command to quarantine a virus"""
    def can_execute(self):
        if not self.args:
            return False, "Which virus do you want to quarantine?"
        return True, None

    def execute(self):
        virus_name = self.args[0].lower()
        result = self.game.player.quarantine(virus_name)
        self.game.turns += 1

        # Check for victory condition
        if len(self.game.player.quarantined_viruses) == len(VIRUS_TYPES):
            self.game.victory = True
            result += "\n\n" + self.game.victory_message()
            self.game.game_over = True

        return result

class HelpCommand(Command):
    """Command to show help message"""
    def execute(self):
        return self.game.show_help()

class QuitCommand(Command):
    """Command to quit the game"""
    def execute(self):
        confirm = input("Are you sure you want to exit? (y/n): ").lower()
        if confirm in ['y', 'yes']:
            self.game.game_over = True
            # Return an empty string to avoid duplicate goodbye messages —
            # the game loop will handle the exit message.
            return ""
        return "Continuing mission..."

class ClearCommand(Command):
    """Command to clear the screen"""
    def execute(self):
        # Import os here to maintain encapsulation
        import os

        # Clear screen based on OS (Windows vs Unix-like)
        os.system('cls' if os.name == 'nt' else 'clear')

        # Return the current location description
        return self.game.player.look()

class MapCommand(Command):
    """Command to display map"""
    def execute(self):
        return self.game.display_map()

class MotherboardCommand(Command):
    """Command to display motherboard diagram"""
    def execute(self):
        return self.game.display_motherboard()

class ReadCommand(Command):
    """Command to read text content of an item"""
    def can_execute(self):
        if not self.args:
            return False, "What do you want to read?"
        return True, None

    def execute(self):
        item_name = self.args[0].lower()

        # Try to match with room items first, then inventory items
        if item_name not in self.game.player.location.items and item_name not in self.game.player.items:
            room_match = self.game._match_item_prefix(item_name)
            inv_match = self.game._match_inventory_item_prefix(item_name)
            # Use the room match if found, otherwise use inventory match
            if room_match in self.game.player.location.items:
                item_name = room_match
            elif inv_match in self.game.player.items:
                item_name = inv_match

        # Check if item is in inventory
        if item_name in self.game.player.items:
            content = self.game.player.items[item_name]
            if content.startswith('#'):
                # Format as proper document if it starts with #
                return content.replace('# ', '').replace('#', '')
            else:
                return content

        # Check if item is in the room
        elif item_name in self.game.player.location.items:
            content = self.game.player.location.items[item_name]
            if content.startswith('#'):
                # Format as proper document if it starts with #
                return content.replace('# ', '').replace('#', '')
            else:
                return content

        else:
            return f"There is no {item_name} to read here."

class AboutCommand(Command):
    """Command to get information about computer components"""
    def can_execute(self):
        if not self.args:
            return False, "What topic would you like information about? Try 'about cpu', 'about memory', etc."
        return True, None

    def execute(self):
        topic = self.args[0].lower()
        return self.game.get_component_info(topic)

class StatusCommand(Command):
    """Command to check progress"""
    def execute(self):
        return self.game.player.check_progress()

class KnowledgeCommand(Command):
    """Command to check knowledge levels"""
    def execute(self):
        return self.game.player.knowledge_report()

class AchievementsCommand(Command):
    """Command to check achievements"""
    def execute(self):
        return self.game.progress.get_progress_report()

class VisualizeCommand(Command):
    """Command to visualize components"""
    def execute(self):
        if not self.args:
            return self.game.handle_visualization()
        else:
            viz_type = self.args[0].lower()
            return self.game.handle_visualization(viz_type)

class SimulateCommand(Command):
    """Command to run simulations"""
    def execute(self):
        if not self.args:
            return "Please specify a simulation type (cpu, memory) or action (step, toggle, reset, stop)."

        sim_action = self.args[0].lower()

        if sim_action in ('cpu', 'memory'):
            from computerquest import config
            if not config.ENABLE_MINIGAMES:
                return ("Minigames are not yet available. "
                        "Track progress in tk-a7098e (Step 4.1).")
            if sim_action == 'cpu':
                return self.game.start_cpu_minigame()
            return self.game.start_memory_minigame()

        # Action for an already-running simulation
        return self.game.handle_simulation(sim_action)

class QuickHelpCommand(Command):
    """Command to display a quick help overlay"""
    def execute(self):
        from computerquest.utils.helpers import Colors

        quick_help = f"""┏━━━━━━━━━━━━━━━━━━━━━ {Colors.YELLOW}{Colors.BOLD}COMMAND REFERENCE{Colors.RESET} ━━━━━━━━━━━━━━━━━━━━━┓
│                                                                      │
│  {Colors.BOLD}Movement:{Colors.RESET}                                                           │
│    {Colors.GREEN}n, s, e, w{Colors.RESET} - Go North, South, East, West                         │
│    {Colors.GREEN}ne, nw, se, sw{Colors.RESET} - Go Northeast, Northwest, Southeast, Southwest   │
│    {Colors.CYAN}u, d{Colors.RESET} - Go Up, Down                                               │
│                                                                      │
│  {Colors.BOLD}Basic Commands:{Colors.RESET}                                                     │
│    {Colors.GREEN}l, look{Colors.RESET} - Examine your surroundings or an item                    │
│    {Colors.GREEN}look [item]{Colors.RESET} - Examine a specific item                             │
│    {Colors.GREEN}i{Colors.RESET} - Check your inventory                                          │
│    {Colors.GREEN}t [item]{Colors.RESET} - Take an item                                           │
│    {Colors.GREEN}drop [item]{Colors.RESET} - Remove an item from your inventory                  │
│    {Colors.GREEN}m{Colors.RESET} - Show map                                                      │
│    {Colors.GREEN}mb{Colors.RESET} - Show motherboard layout                                      │
│    {Colors.GREEN}c{Colors.RESET} - Clear screen                                                  │
│                                                                      │
│  {Colors.BOLD}Security Functions:{Colors.RESET}                                                 │
│    {Colors.GREEN}sc, scan{Colors.RESET} - Scan for viruses in current location                   │
│    {Colors.GREEN}scan [item]{Colors.RESET} - Check if an item contains a virus                   │
│    {Colors.GREEN}quarantine [virus]{Colors.RESET} - Contain a discovered virus                   │
│    {Colors.GREEN}advscan{Colors.RESET} - Perform advanced scan (requires decoder_tool)           │
│                                                                      │
│  {Colors.BOLD}Information & Progress:{Colors.RESET}                                             │
│    {Colors.GREEN}status{Colors.RESET} - Check your virus discovery progress                      │
│    {Colors.GREEN}knowledge{Colors.RESET} - View your computer architecture knowledge             │
│    {Colors.GREEN}about [topic]{Colors.RESET} - Get information about a computer component        │
│    {Colors.GREEN}achievements{Colors.RESET} - View your achievements and progress                │
│                                                                      │
│  {Colors.BOLD}Educational Features:{Colors.RESET}                                               │
│    {Colors.GREEN}viz [comp]{Colors.RESET} - Show visualization of a component                    │
│    {Colors.GREEN}simulate cpu{Colors.RESET} - Start CPU pipeline simulation                      │
│    {Colors.GREEN}simulate memory{Colors.RESET} - Start memory hierarchy simulation               │
│                                                                      │
│  {Colors.BOLD}System Commands:{Colors.RESET}                                                    │
│    {Colors.GREEN}help, h{Colors.RESET} - Show full help message                                  │
│    {Colors.GREEN}q{Colors.RESET} - Quit game                                                     │
│                                                                      │
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

{Colors.BOLD}TIP:{Colors.RESET} Use {Colors.BOLD}Tab{Colors.RESET} key for command completion and {Colors.BOLD}Up/Down arrows{Colors.RESET} for command history!"""
        return quick_help

class CommandProcessor:
    """Processes user commands using Command pattern"""
    def __init__(self, game):
        self.game = game

        # List of direction words for tab completion
        self.direction_words = [
            'north', 'south', 'east', 'west',
            'northeast', 'northwest', 'southeast', 'southwest',
            'up', 'down',
            'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw', 'u', 'd'
        ]

        self.commands = {
            'go': MoveCommand,
            'move': MoveCommand,
            'north': self._direction_command('north'),
            'n': self._direction_command('north'),
            'south': self._direction_command('south'),
            's': self._direction_command('south'),
            'east': self._direction_command('east'),
            'e': self._direction_command('east'),
            'west': self._direction_command('west'),
            'w': self._direction_command('west'),
            'northeast': self._direction_command('northeast'),
            'ne': self._direction_command('northeast'),
            'northwest': self._direction_command('northwest'),
            'nw': self._direction_command('northwest'),
            'southeast': self._direction_command('southeast'),
            'se': self._direction_command('southeast'),
            'southwest': self._direction_command('southwest'),
            'sw': self._direction_command('southwest'),
            'up': self._direction_command('up'),
            'u': self._direction_command('up'),
            'down': self._direction_command('down'),
            'd': self._direction_command('down'),
            'look': LookCommand,
            'l': LookCommand,
            'examine': LookCommand,
            'ex': LookCommand,
            'take': TakeCommand,
            't': TakeCommand,
            'get': TakeCommand,
            'drop': DropCommand,
            'inventory': InventoryCommand,
            'i': InventoryCommand,
            'scan': ScanCommand,
            'sc': ScanCommand,
            'advscan': AdvancedScanCommand,
            'advanced-scan': AdvancedScanCommand,
            'advanced_scan': AdvancedScanCommand,
            'analyze': AnalyzeCommand,
            'quarantine': QuarantineCommand,
            'help': HelpCommand,
            'h': HelpCommand,
            '?': QuickHelpCommand,
            'quit': QuitCommand,
            'exit': QuitCommand,
            'q': QuitCommand,
            'map': MapCommand,
            'm': MapCommand,
            'motherboard': MotherboardCommand,
            'mb': MotherboardCommand,
            'read': ReadCommand,
            'r': ReadCommand,
            'about': AboutCommand,
            'status': StatusCommand,
            'progress': StatusCommand,
            'knowledge': KnowledgeCommand,
            'achievements': AchievementsCommand,
            'achieve': AchievementsCommand,
            'stats': AchievementsCommand,
            'visualize': VisualizeCommand,
            'viz': VisualizeCommand,
            'simulate': SimulateCommand,
            'sim': SimulateCommand,
            'clear': ClearCommand,
            'cls': ClearCommand,
            'c': ClearCommand,
        }

    def _direction_command(self, direction):
        """Create a move command with direction already specified"""
        def command_factory(game, args=None):
            return MoveCommand(game, [direction])
        return command_factory

    def preprocess_command(self, user_input):
        """
        Preprocess command for common typos and normalization
        Returns corrected command string
        """
        # Remove extra whitespace
        processed = user_input.strip().lower()

        # Handle common typos and variations
        typo_corrections = {
            # Direction typos
            'nort': 'north', 'norht': 'north', 'nrth': 'north', 'noth': 'north',
            'sout': 'south', 'souht': 'south', 'suth': 'south', 'souh': 'south',
            'easr': 'east', 'eas': 'east', 'esat': 'east', 'est': 'east',
            'wesr': 'west', 'wets': 'west', 'wst': 'west', 'wes': 'west',
            'norteast': 'northeast', 'northeat': 'northeast', 'norhteast': 'northeast',
            'nortwest': 'northwest', 'northwet': 'northwest', 'norhtwest': 'northwest',
            'souteast': 'southeast', 'southeat': 'southeast', 'souhteast': 'southeast',
            'soutwest': 'southwest', 'southwet': 'southwest', 'souhtwest': 'southwest',

            # Command typos
            'lok': 'look', 'loook': 'look', 'luk': 'look', 'loo': 'look',
            'invntory': 'inventory', 'invetory': 'inventory', 'inv': 'inventory',
            'tak': 'take', 'tke': 'take', 'tkae': 'take',
            'hlp': 'help', 'hlep': 'help', 'hel': 'help',
            'mp': 'map', 'mpa': 'map',
            'qit': 'quit', 'qt': 'quit', 'ext': 'exit',
            'scn': 'scan', 'sacan': 'scan',
            'clr': 'clear', 'clar': 'clear', 'clera': 'clear',
        }

        # Check if the first word is a known typo
        words = processed.split()
        if words and words[0] in typo_corrections:
            words[0] = typo_corrections[words[0]]
            processed = ' '.join(words)

        return processed

    def process(self, user_input):
        """Process a user command"""
        # Skip empty inputs
        if not user_input.strip():
            return "Please enter a command. Type 'help' for available commands."

        # Preprocess command for typos
        processed_input = self.preprocess_command(user_input)

        # Split into command words
        cmd_words = processed_input.split()
        command = cmd_words[0]
        args = cmd_words[1:]

        # Apply command prefix matching
        command = self.game._match_command_prefix(command)

        # Check if command exists
        if command in self.commands:
            cmd_class = self.commands[command]
            cmd = cmd_class(self.game, args)

            # Validate command
            can_execute, error = cmd.can_execute() if hasattr(cmd, 'can_execute') else (True, None)
            if not can_execute:
                return error

            # Execute command
            result = cmd.execute()

            # Check for new achievements
            newly_unlocked = self.game.progress.update()
            if newly_unlocked:
                result += "\n\nACHIEVEMENT UNLOCKED!\n"
                for achievement in newly_unlocked:
                    result += f"- {achievement.name}: {achievement.description}\n"

            return result
        else:
            # Try to find similarly named commands (fuzzy matching)
            from computerquest.utils.helpers import Colors
            similar_commands = []
            for cmd in self.commands.keys():
                # Simple similarity check - more than half of letters match
                if len(cmd) > 2 and sum(c in command for c in cmd) >= len(cmd) // 2:
                    similar_commands.append(cmd)

            if similar_commands:
                suggestions = ', '.join([f"{Colors.GREEN}{cmd}{Colors.RESET}" for cmd in similar_commands[:3]])
                return f"Command '{command}' not recognized. Did you mean: {suggestions}?\nType 'help' for available commands."
            else:
                return f"Command '{command}' not recognized. Type 'help' for available commands."
