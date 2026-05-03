"""
Component class (formerly Room)

Represents a computer component that can be visited by the player.
"""

from computerquest.config import DIRECTION_NAMES


class Component:
    def __init__(self, name="", description="", lit=False, iden="000", save=False):
        """
        Constructor: create a new Component object representing a computer component
        name: name of component
        description: component description
        lit: if the component is "lit" (accessible without special tools)
        iden: unique identifier
        save: whether this component's state needs to be saved
        """
        self.name = name  # Component name
        self.desc1 = description  # Original description (unchangeable)
        self.desc = description   # Current description (changeable)
        self.door = {}  # Special connection points requiring actions to traverse
        self.doors = {} # Regular connections to other components
        self.openDoors = []  # List of all connections with other components
        self.items = {}  # Items/data in this component
        self.play = []  # List of entities in this component
        self.lit = lit    # If component is accessible without special tools
        self.save = save  # If component state needs saving
        self.id = iden   # Component identifier
        self.security_level = 0  # Security restriction level (0=none, 1=user, 2=admin, 3=system)
        self.data_types = []  # Types of data typically found in this component
        self.performance = {  # Performance characteristics
            "speed": 0,       # 1-10 scale
            "capacity": 0,    # 1-10 scale
            "reliability": 0  # 1-10 scale
        }
        self.visited = False  # Has player visited this component
        self.power_state = "on"  # Power state of the component (on/off/sleep)
        self.error_state = None  # Any error conditions present

    def set_specs(self, security=0, data_types=None, speed=0, capacity=0, reliability=0):
        """Set technical specifications for this computer component"""
        self.security_level = security
        self.data_types = data_types or []
        self.performance["speed"] = speed
        self.performance["capacity"] = capacity
        self.performance["reliability"] = reliability

    def connect_to(self, other, direction):
        """
        Connect this component to another component via a data path
        other: the component to connect to
        direction: direction identifier (n, s, e, w, etc.)
        """
        # Check if connection already exists
        if other.id in [list(d.keys())[0].id for d in self.openDoors if d]:
            return

        # Add directional connection
        self.doors.update({direction: other})

        # Create connection record
        connect = {other: direction}
        self.openDoors.append(connect)

    def add_items(self, item):
        """
        Add items/data to this component
        item: dictionary with name/description pairs
        """
        # Add items to component
        self.items.update(item)

    def add_door(self, name, d, od, door):
        """
        Add a special connection requiring action to use
        name: name of the connection
        d: direction from this component
        od: direction from other component
        door: the component to connect to
        """
        self.door.update({name: [d, door, od]})

        # Update description
        if "connection" not in self.desc.lower():
            self.desc += f" There's a {name} connection that appears to require authentication."

    def print_details(self):
        """
        Generate detailed description of the component
        including connections and contents
        """
        # Component name
        s = f"== {self.name} ==\n"

        # Main description
        s += f"{self.desc}\n"

        # Create visual compass for directions
        if self.doors:
            # Get directions
            has_n = 'n' in self.doors
            has_s = 's' in self.doors
            has_e = 'e' in self.doors
            has_w = 'w' in self.doors
            has_ne = 'ne' in self.doors
            has_nw = 'nw' in self.doors
            has_se = 'se' in self.doors
            has_sw = 'sw' in self.doors
            has_u = 'u' in self.doors
            has_d = 'd' in self.doors

            # Build compass
            s += "\n" + "=" * 20 + " AVAILABLE CONNECTIONS " + "=" * 20 + "\n\n"

            # Show diagonal directions in first row
            s += "      "
            s += f"NW: {self.doors['nw'].name}" if has_nw else "     "
            s += "     "
            s += f"N: {self.doors['n'].name}" if has_n else "     "
            s += "     "
            s += f"NE: {self.doors['ne'].name}" if has_ne else "     "
            s += "\n"

            # Middle row for W, current location, E
            s += "      "
            s += f"W: {self.doors['w'].name}" if has_w else "     "
            s += "  <--[ YOU ARE HERE ]-->  "
            s += f"E: {self.doors['e'].name}" if has_e else "     "
            s += "\n"

            # Bottom row for SW, S, SE
            s += "      "
            s += f"SW: {self.doors['sw'].name}" if has_sw else "     "
            s += "     "
            s += f"S: {self.doors['s'].name}" if has_s else "     "
            s += "     "
            s += f"SE: {self.doors['se'].name}" if has_se else "     "
            s += "\n"

            # Special directions
            if has_u or has_d:
                s += "\nSpecial Connections:\n"
                if has_u:
                    s += f"- Up: {self.doors['u'].name}\n"
                if has_d:
                    s += f"- Down: {self.doors['d'].name}\n"

            # Detailed list of connections
            s += "\nDetailed Connections:\n"
            for d, r in self.doors.items():
                # Get readable direction name
                di = DIRECTION_NAMES.get(d, d)

                # Add connection information
                s += f"- {di}: {r.name}\n"

        # Items/data in this component
        if self.items:
            s += "\n" + "=" * 20 + " COMPONENTS PRESENT " + "=" * 22 + "\n\n"
            for i in self.items:
                s += f"- {i}\n"

            s += "\nType 'examine [component]' or 'take [component]' to interact."

        # Technical details if player has advanced knowledge
        if self.visited:
            s += "\n" + "=" * 20 + " TECHNICAL DETAILS " + "=" * 23 + "\n\n"

            if self.security_level > 0:
                s += f"- Security Level: {self.security_level}\n"
            if self.data_types:
                s += f"- Data Types: {', '.join(self.data_types)}\n"
            if any(self.performance.values()):
                s += "- Performance Metrics:\n"
                for metric, value in self.performance.items():
                    if value > 0:
                        s += f"  * {metric.capitalize()}: {value}/10\n"
        else:
            s += "\nHint: Use 'scan' to learn more technical details about this component."

        return s

    def mark_visited(self):
        """Mark this component as visited to reveal more details on subsequent visits"""
        self.visited = True

    def error(self, error_description):
        """Set component to error state"""
        self.error_state = error_description
        self.desc = f"ERROR: {error_description}\n\n" + self.desc

    def repair(self):
        """Clear error state"""
        self.error_state = None
        self.desc = self.desc1  # Reset to original description
