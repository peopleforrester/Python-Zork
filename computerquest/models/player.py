"""
Player class

Represents the player character in the game.
"""

from __future__ import annotations

from typing import Any

from computerquest.config import INVENTORY_LIMIT, MAX_HEALTH, MAX_KNOWLEDGE, is_virus_name


class Player:
    def __init__(
        self,
        location: Any = None,
        items: dict[str, Any] | None = None,
        NPC: bool = False,
        name: str | None = None,
    ) -> None:
        """
        Player constructor
        location: starting location for the player
        items: starting items for the player
        NPC: defines if player object is an NPC or not
        name: player name
        """
        self.location = location  # Current component location
        self.items = items or {}  # Player inventory
        self.max_health = MAX_HEALTH
        self.health = MAX_HEALTH
        self.com = NPC  # Is this an NPC?
        self.name = name  # Player name
        self.death = False  # Is player dead?

        # System-specific attributes
        self.found_viruses: list[str] = []
        # Microquiz progress: ids from the puzzle registry.
        self.solved_puzzles: set[str] = set()
        self.attempted_puzzles: set[str] = set()
        self.quarantined_viruses: list[str] = []
        self.knowledge = {
            "cpu": 0,
            "memory": 0,
            "storage": 0,
            "networking": 0,
            "security": 0
        }

        # Add player to location's entities list if this is an NPC
        if self.com:
            self.location.play.append(self)

    def __str__(self) -> str:
        """String representation of Player"""
        return self.name if self.name else "Security Program"

    def go(self, direction: str) -> bool:
        """
        Move in a direction
        Returns: True if successful, False otherwise
        """
        room = self.location  # Current component
        direct = list(room.doors)  # Available directions

        if direction in direct:
            self.location = room.doors[direction]  # Move to new location

            # Update NPC list if this is an NPC
            if self.com:
                room.play.remove(self)
                self.location.play.append(self)

            return True
        else:
            return False

    def look(self, item: str | None = None) -> str:
        """
        Look around, or look at a specific item
        item: Optional item to examine
        Returns: Text description of what is seen
        """
        room = self.location  # Current component

        # Looking at a specific item
        if item is not None:
            # First check in the room
            if item in room.items:
                item_desc = room.items[item]
                return f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━ {item} ━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n\n{item_desc}\n\nType 'take {item}' to pick it up, or 'read {item}' if it's readable.\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

            # Then check inventory
            elif item in self.items:
                item_desc = self.items[item]
                return f"┏━━━━━━━━━━━━━━━━━━━ {item} (in your inventory) ━━━━━━━━━━━━━━━━━━━┓\n\n{item_desc}\n\nType 'drop {item}' to remove it from your inventory.\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

            # Not found
            else:
                return f'Item "{item}" not found in this location or your inventory.'

        # Looking around the room
        else:
            # Generate technical details if the component has been visited
            technical_details = None
            if room.visited:
                technical_details = []
                if room.security_level > 0:
                    technical_details.append(f"Security Level: {room.security_level}")
                if room.data_types:
                    technical_details.append(f"Data Types: {', '.join(room.data_types)}")
                if any(room.performance.values()):
                    technical_details.append("Performance Metrics:")
                    for metric, value in room.performance.items():
                        if value > 0:
                            technical_details.append(f"  * {metric.capitalize()}: {value}/10")

            # Use the new formatted output
            from computerquest.utils.helpers import format_look_output
            return format_look_output(
                location=room,
                connections=room.doors,
                items=list(room.items.keys()),
                technical_details=technical_details,
                player=self,
            )

    def take(self, item: str) -> str:
        """
        Take an item from the current location
        item: Item to take
        Returns: Confirmation message
        """
        # Check for inventory limit (>= so the cap holds even if items were
        # seeded via construction or direct dict assignment).
        if len(self.items) >= INVENTORY_LIMIT:
            return "Your inventory is full. Drop something first."

        # Check if item is in the room
        if item in self.location.items:
            # Move item from room to inventory
            self.items.update({item: self.location.items.pop(item)})
            return f"Taken: {item}"

        # Check if item is in a container in the room
        for _container_key, v in self.location.items.items():
            if isinstance(v, dict):
                for inner_name in list(v):
                    if inner_name == item:
                        v.pop(inner_name)
                        return f"Taken: {item}"

        return f"There is no {item} here to take."

    def drop(self, item: str) -> str:
        """
        Drop an item from inventory to current location
        item: Item to drop
        Returns: Confirmation message
        """
        if item in self.items:
            # Get item description
            desc = self.items[item]

            # Remove from inventory and add to room
            self.items.pop(item)
            self.location.items.update({item: desc})

            return f"Dropped: {item}"
        else:
            return f"You don't have {item} in your inventory."

    def scan(self, target: str | None = None) -> str:
        """
        Scan for viruses in current location or specific item
        target: Optional item to scan
        Returns: Scan results
        """
        # Check for required tool
        if 'antivirus_tool' not in self.items:
            return "You need an antivirus tool to perform a scan."

        # Scanning a specific item
        if target:
            # Check if item is in room
            if target in self.location.items:
                if is_virus_name(target):
                    self._record_virus_found(target)
                    return f"ALERT! {target} detected. This is a malicious program that should be quarantined immediately."
                else:
                    return f"No virus detected in {target}."

            # Check if item is in inventory
            elif target in self.items:
                if is_virus_name(target):
                    self._record_virus_found(target)
                    return f"ALERT! {target} detected. This is a malicious program in your inventory that should be quarantined immediately."
                else:
                    return f"No virus detected in {target}."
            else:
                return f"There's no {target} here to scan."

        # Scanning the entire location
        else:
            # Check for viruses
            viruses_here = [item for item in self.location.items if is_virus_name(item)]

            if viruses_here:
                result = "SECURITY ALERT! Virus scan detected the following threats:\n"
                for virus in viruses_here:
                    self._record_virus_found(virus)
                    result += f"- {virus}\n"
                result += "\nUse 'quarantine [virus]' to contain these threats."
                return result
            else:
                return "Scan complete. No viruses detected in this location."

    def advanced_scan(self, target: str | None = None) -> str:
        """
        Perform advanced scan for hidden threats
        target: Optional item to scan
        Returns: Advanced scan results
        """
        # Check for required tools
        required_tools = {
            'antivirus_tool': "You need an antivirus tool to perform a scan.",
            'decoder_tool': "A more advanced decoder tool would help analyze code patterns."
        }

        missing_tools = [tool for tool, msg in required_tools.items() if tool not in self.items]
        if missing_tools:
            return required_tools[missing_tools[0]]

        # Knowledge requirements by component type
        required_knowledge = {
            'cpu': {'cpu': 2, 'security': 1},
            'memory': {'memory': 2, 'security': 1},
            'storage': {'storage': 2, 'security': 1},
            'network': {'networking': 2, 'security': 1},
            'firmware': {'security': 3}
        }

        # Determine component type
        component_type = self._determine_component_type()

        # Check knowledge requirements
        if component_type in required_knowledge:
            for knowledge_area, level in required_knowledge[component_type].items():
                if self.knowledge[knowledge_area] < level:
                    return f"You need more knowledge of {knowledge_area} (level {level}) to perform an advanced scan in this component."

        # Scanning a specific item
        if target:
            return self._advanced_scan_item(target)

        # Scanning the entire location
        return self._advanced_scan_location()

    def _advanced_scan_item(self, target: str) -> str:
        """Helper method for advanced scanning an item"""
        # Check in room
        if target in self.location.items:
            item_desc = self.location.items[target]
            return self._analyze_item_for_threats(target, item_desc)

        # Check in inventory
        elif target in self.items:
            item_desc = self.items[target]
            return self._analyze_item_for_threats(target, item_desc, in_inventory=True)

        else:
            return f"There's no {target} here to scan."

    def _advanced_scan_location(self) -> str:
        """Helper method for advanced scanning current location"""
        # Find canonical viruses
        viruses_here = [item for item in self.location.items if is_virus_name(item)]

        # Find suspicious items — items not flagged as canonical viruses but
        # with hint words in their description.
        hidden_threats = []
        for item, desc in self.location.items.items():
            if not is_virus_name(item) and (
                'suspicious' in desc.lower() or 'malicious' in desc.lower()
            ):
                hidden_threats.append(item)

        if viruses_here or hidden_threats:
            result = "ADVANCED SECURITY SCAN RESULTS:\n\n"

            if viruses_here:
                result += "Confirmed threats:\n"
                for virus in viruses_here:
                    self._record_virus_found(virus)
                    result += f"- {virus}\n"

            if hidden_threats:
                result += "\nSuspicious items requiring further analysis:\n"
                for item in hidden_threats:
                    result += f"- {item}\n"

            result += "\nUse 'analyze [item]' for detailed threat assessment and 'quarantine [virus]' to contain threats."
            return result
        else:
            return f"Advanced scan complete. No threats detected in {self.location.name}."

    def _analyze_item_for_threats(self, item_name: str, item_desc: str, in_inventory: bool = False) -> str:
        """Analyze an item for virus signatures"""
        location = "in your inventory" if in_inventory else ""

        # Check for virus indicators: canonical names, or hint words in desc.
        if is_virus_name(item_name) or 'malicious' in item_desc.lower() or 'suspicious' in item_desc.lower():
            virus_type = self._detect_virus_type(item_name, item_desc)

            if virus_type:
                self._record_virus_found(virus_type)

            return f"ADVANCED SCAN RESULTS:\n\nThreat detected {location} in {item_name}!\n" + \
                   f"Virus Type: {virus_type if virus_type else 'Unknown'}\n" + \
                   "Threat Level: High\n" + \
                   f"Analysis: {item_desc}\n\n" + \
                   "Recommended action: Quarantine immediately."
        else:
            return f"Advanced scan complete. No threats detected in {item_name}."

    def _detect_virus_type(self, item_name: str, item_desc: str) -> str | None:
        """Determine virus type from item characteristics"""
        if 'boot' in item_name.lower() or 'boot' in item_desc.lower():
            return "boot_sector_virus"
        elif 'root' in item_name.lower() or 'kernel' in item_desc.lower():
            return "rootkit_virus"
        elif 'memory' in item_name.lower() or 'ram' in item_desc.lower():
            return "memory_resident_virus"
        elif 'firm' in item_name.lower() or 'bios' in item_desc.lower():
            return "firmware_virus"
        elif 'packet' in item_name.lower() or 'network' in item_desc.lower():
            return "packet_sniffer_virus"
        return None

    def _determine_component_type(self) -> str:
        """Determine the type of the current component"""
        loc_name = self.location.name.lower()

        if any(x in loc_name for x in ['cpu', 'alu', 'control', 'register']):
            return 'cpu'
        elif any(x in loc_name for x in ['memory', 'ram', 'cache']):
            return 'memory'
        elif any(x in loc_name for x in ['ssd', 'hdd', 'drive', 'disk', 'storage']):
            return 'storage'
        elif any(x in loc_name for x in ['network', 'interface']):
            return 'network'
        elif any(x in loc_name for x in ['bios', 'firmware', 'uefi']):
            return 'firmware'
        return 'other'

    def _record_virus_found(self, virus: str) -> None:
        """Record a found virus and update knowledge"""
        if virus not in self.found_viruses:
            self.found_viruses.append(virus)

    def quarantine(self, virus_name: str) -> str:
        """
        Quarantine a detected virus
        virus_name: Name of virus to quarantine
        Returns: Quarantine result message
        """
        # Check for required tool
        if 'antivirus_tool' not in self.items:
            return "You need an antivirus tool to quarantine viruses."

        # Check if virus has been found
        if virus_name not in self.found_viruses:
            return f"You haven't detected a virus named '{virus_name}' yet. Try scanning first."

        # Check if already quarantined
        if virus_name in self.quarantined_viruses:
            return f"The {virus_name} has already been quarantined."

        # Check if virus is in current location
        if virus_name in self.location.items:
            # Remove the virus
            self.location.items.pop(virus_name)

            # Add to quarantined list
            self.quarantined_viruses.append(virus_name)

            # Add neutralized version
            self.location.items[f"quarantined_{virus_name}"] = f"A neutralized version of {virus_name}, safely contained and no longer a threat."


            return f"Success! The {virus_name} has been quarantined and can no longer harm the system."

        # Check if virus is in inventory
        elif virus_name in self.items:
            # Remove the virus
            self.items.pop(virus_name)

            # Add to quarantined list
            self.quarantined_viruses.append(virus_name)

            # Add neutralized version
            self.items[f"quarantined_{virus_name}"] = f"A neutralized version of {virus_name}, safely contained and no longer a threat."


            return f"Success! The {virus_name} has been quarantined from your inventory and can no longer harm the system."

        else:
            return f"The {virus_name} is not in this location. You need to find where it's hiding."

    def analyze(self, target: str) -> str:
        """
        Deeply analyze an item to reveal hidden properties
        target: Item to analyze
        Returns: Analysis results
        """
        if 'decoder_tool' not in self.items:
            return "You need a decoder tool to perform detailed analysis."

        # Check item location
        if target in self.location.items:
            return self._analyze_item(target, self.location.items[target])
        elif target in self.items:
            return self._analyze_item(target, self.items[target], in_inventory=True)
        else:
            return f"There's no {target} here to analyze."

    def _analyze_item(self, item_name: str, item_desc: str, in_inventory: bool = False) -> str:
        """Helper method to analyze an item"""
        location = " in your inventory" if in_inventory else ""

        # Special analysis for different item types
        if 'log' in item_name:
            return self._analyze_log(item_name, item_desc)
        elif 'calculation' in item_name or 'anomaly' in item_name:
            return self._analyze_calculation(item_name, item_desc)
        elif 'packet' in item_name:
            return self._analyze_packet(item_name, item_desc)
        else:
            # Generic analysis
            return self._analyze_generic(item_name, item_desc, location)

    def _analyze_log(self, name: str, desc: str) -> str:
        """Analyze a log file"""
        suspicious = 'suspicious' in desc or 'unusual' in desc
        activity_type = 'suspicious' if suspicious else 'normal'

        return f"Analysis of {name}:\n\n" + \
               f"The log contains entries showing {desc}\n" + \
               f"Pattern analysis reveals evidence of {activity_type} activity."

    def _analyze_calculation(self, name: str, desc: str) -> str:
        """Analyze calculation or anomaly data"""
        suspicious = 'suspicious' in desc or 'unusual' in desc
        finding = 'virus attempting to hide its operations' if suspicious else 'normal system process'

        return f"Analysis of {name}:\n\n" + \
               f"The data patterns show {desc}\n" + \
               f"This could be a sign of a {finding}."

    def _analyze_packet(self, name: str, desc: str) -> str:
        """Analyze network packet data"""
        suspicious = 'suspicious' in desc or 'unusual' in desc
        traffic_type = 'data exfiltration' if suspicious else 'normal network traffic'

        return f"Analysis of {name}:\n\n" + \
               f"The packet contains {desc}\n" + \
               f"Traffic analysis indicates this may be {traffic_type}."

    def _analyze_generic(self, name: str, desc: str, location: str = "") -> str:
        """Generic item analysis"""
        suspicious_terms = ['suspicious', 'unusual', 'strange', 'abnormal', 'unexpected']
        is_suspicious = any(term in desc.lower() for term in suspicious_terms)

        if is_suspicious:
            virus_hint = self._get_virus_hint(desc)

            return f"Analysis of {name}{location}:\n\n" + \
                  "SECURITY ALERT: This item shows signs of suspicious activity.\n" + \
                  f"Details: {desc}\n" + \
                  f"{virus_hint}"
        else:
            return f"Analysis of {name}{location}:\n\n" + \
                  f"No suspicious patterns detected. This appears to be a normal {name}.\n" + \
                  f"Description: {desc}"

    def _get_virus_hint(self, desc: str) -> str:
        """Get hint about potential virus type"""
        if 'boot' in desc.lower():
            return "This may be related to a boot sector infection."
        elif 'kernel' in desc.lower() or 'root' in desc.lower():
            return "This could indicate rootkit activity in the system."
        elif 'memory' in desc.lower():
            return "This pattern is consistent with memory-resident malware."
        elif 'firmware' in desc.lower() or 'bios' in desc.lower():
            return "This suggests possible firmware compromising."
        elif 'network' in desc.lower() or 'packet' in desc.lower():
            return "This is characteristic of network traffic interception."
        return ""

    def check_progress(self) -> str:
        """Check progress on virus discovery and quarantine"""
        from computerquest.config import VIRUS_TYPES

        # Calculate progress bar for viruses found
        found_bar = "█" * len(self.found_viruses) + "░" * (len(VIRUS_TYPES) - len(self.found_viruses))
        quarantined_bar = "█" * len(self.quarantined_viruses) + "░" * (len(VIRUS_TYPES) - len(self.quarantined_viruses))

        result = "┏━━━━━━━━━━━━━━━ MISSION STATUS REPORT ━━━━━━━━━━━━━━━┓\n"
        result += f"  Viruses Found: {found_bar} {len(self.found_viruses)}/{len(VIRUS_TYPES)}\n"

        if self.found_viruses:
            result += "  Detected Viruses:\n"
            for virus in self.found_viruses:
                result += f"    • {virus}\n"

        result += f"\n  Viruses Quarantined: {quarantined_bar} {len(self.quarantined_viruses)}/{len(VIRUS_TYPES)}\n"
        if self.quarantined_viruses:
            result += "  Neutralized Viruses:\n"
            for virus in self.quarantined_viruses:
                result += f"    • {virus}\n"

        # Breadcrumb path - Show current location context
        from computerquest.utils.helpers import truncate_desc
        if hasattr(self.location, 'name'):
            result += "\n  Current Location Path:\n"
            result += f"    {self.location.name} ({truncate_desc(self.location.desc, 40)})\n"

        result += "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

        return result

    def knowledge_report(self) -> str:
        """Display knowledge gained about computer architecture"""
        total = sum(self.knowledge.values())

        result = "┏━━━━━━━━━━━━ COMPUTER ARCHITECTURE KNOWLEDGE ━━━━━━━━━━━━┓\n"

        for topic, level in self.knowledge.items():
            # Levels are fractional since the puzzle cutover (difficulty
            # weights add 1, 1.5, or 2). Render whole symbols and show the
            # exact value alongside.
            whole = int(level)
            stars = "★" * whole + "☆" * (MAX_KNOWLEDGE - whole)
            level_bar = "█" * whole + "░" * (MAX_KNOWLEDGE - whole)
            result += f"  {topic.capitalize()}: {stars} {level_bar} {level}/{MAX_KNOWLEDGE}\n"

        # Total progress bar
        max_total = len(self.knowledge) * MAX_KNOWLEDGE
        progress_percent = (total / max_total) * 100
        progress_bar = "█" * int(progress_percent/10) + "░" * (10 - int(progress_percent/10))

        result += f"\n  Overall Progress: {progress_bar} {progress_percent:.1f}%"
        result += f"\n  Total Knowledge: {total}/{max_total}"
        result += "\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"

        return result

    def _increase_component_knowledge(self) -> None:
        """Increase knowledge based on current component type"""
        component_type = self._determine_component_type()

        if component_type == 'cpu':
            self.knowledge['cpu'] = min(MAX_KNOWLEDGE, self.knowledge['cpu'] + 1)
        elif component_type == 'memory':
            self.knowledge['memory'] = min(MAX_KNOWLEDGE, self.knowledge['memory'] + 1)
        elif component_type == 'storage':
            self.knowledge['storage'] = min(MAX_KNOWLEDGE, self.knowledge['storage'] + 1)
        elif component_type == 'network':
            self.knowledge['networking'] = min(MAX_KNOWLEDGE, self.knowledge['networking'] + 1)
