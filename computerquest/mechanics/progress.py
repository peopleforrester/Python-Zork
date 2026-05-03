"""
Progress tracking system

Handles player achievements and progress tracking
"""

from computerquest.config import MAX_KNOWLEDGE, VIRUS_TYPES


class Achievement:
    """Represents a game achievement that can be unlocked"""
    def __init__(self, id, name, description, condition_fn, reward=None):
        self.id = id
        self.name = name
        self.description = description
        self.condition_fn = condition_fn  # Function that returns True when achieved
        self.unlocked = False
        self.unlock_time = None
        self.reward = reward  # Optional reward (item, knowledge, etc.)

class ProgressSystem:
    """Tracks player progress and manages achievements"""
    def __init__(self, game):
        self.game = game
        self.achievements = []
        self.exploration_progress = 0  # Percentage of map explored
        self.knowledge_progress = 0    # Percentage of total knowledge gained
        self.virus_progress = 0        # Percentage of viruses found/quarantined
        self.total_score = 0

        # Setup achievements
        self.setup_achievements()

    def setup_achievements(self):
        """Define all achievements for the game"""
        self.achievements = [
            Achievement(
                "first_step",
                "First Steps",
                "Visit your first new component after the CPU Core",
                lambda: len([r for r in self.game.game_map.rooms.values() if r.visited]) > 1
            ),
            Achievement(
                "explorer",
                "System Explorer",
                "Visit at least 10 different components",
                lambda: len([r for r in self.game.game_map.rooms.values() if r.visited]) >= 10
            ),
            Achievement(
                "master_explorer",
                "System Cartographer",
                "Visit all system components",
                lambda: all(r.visited for r in self.game.game_map.rooms.values())
            ),
            Achievement(
                "first_virus",
                "Threat Detector",
                "Find your first virus",
                lambda: len(self.game.player.found_viruses) >= 1
            ),
            Achievement(
                "virus_hunter",
                "Virus Hunter",
                "Find all viruses in the system",
                lambda: len(self.game.player.found_viruses) >= len(VIRUS_TYPES)
            ),
            Achievement(
                "first_quarantine",
                "Security Specialist",
                "Successfully quarantine your first virus",
                lambda: len(self.game.player.quarantined_viruses) >= 1
            ),
            Achievement(
                "system_savior",
                "System Savior",
                "Quarantine all viruses and save the system",
                lambda: len(self.game.player.quarantined_viruses) >= len(VIRUS_TYPES)
            ),
            Achievement(
                "cpu_expert",
                "CPU Architecture Expert",
                "Reach maximum knowledge of CPU components",
                lambda: self.game.player.knowledge['cpu'] >= MAX_KNOWLEDGE
            ),
            Achievement(
                "memory_expert",
                "Memory Systems Expert",
                "Reach maximum knowledge of memory systems",
                lambda: self.game.player.knowledge['memory'] >= MAX_KNOWLEDGE
            ),
            Achievement(
                "storage_expert",
                "Storage Expert",
                "Reach maximum knowledge of storage systems",
                lambda: self.game.player.knowledge['storage'] >= MAX_KNOWLEDGE
            ),
            Achievement(
                "network_expert",
                "Networking Expert",
                "Reach maximum knowledge of network components",
                lambda: self.game.player.knowledge['networking'] >= MAX_KNOWLEDGE
            ),
            Achievement(
                "security_expert",
                "Security Expert",
                "Reach maximum knowledge of security concepts",
                lambda: self.game.player.knowledge['security'] >= MAX_KNOWLEDGE
            ),
            Achievement(
                "computer_scientist",
                "Computer Scientist",
                "Reach maximum knowledge in all areas",
                lambda: all(level >= MAX_KNOWLEDGE for level in self.game.player.knowledge.values())
            ),
            Achievement(
                "efficient",
                "Efficient Operator",
                "Complete the game in under 50 turns",
                lambda: self.game.victory and self.game.turns < 50
            ),
        ]

    def update(self):
        """
        Update progress metrics and check for newly unlocked achievements
        Should be called after each player action
        Returns: List of newly unlocked achievements
        """
        # Update exploration progress
        visited_rooms = len([r for r in self.game.game_map.rooms.values() if r.visited])
        total_rooms = len(self.game.game_map.rooms)
        self.exploration_progress = int((visited_rooms / total_rooms) * 100)

        # Update knowledge progress
        current_knowledge = sum(self.game.player.knowledge.values())
        max_knowledge = len(self.game.player.knowledge) * MAX_KNOWLEDGE  # MAX_KNOWLEDGE is max level per area
        self.knowledge_progress = int((current_knowledge / max_knowledge) * 100)

        # Update virus progress - considered 50% for finding, 50% for quarantining
        viruses_found_pct = len(self.game.player.found_viruses) / len(VIRUS_TYPES) * 50
        viruses_quarantined_pct = len(self.game.player.quarantined_viruses) / len(VIRUS_TYPES) * 50
        self.virus_progress = int(viruses_found_pct + viruses_quarantined_pct)

        # Calculate total score
        self.total_score = self.calculate_score()

        # Check for newly unlocked achievements
        newly_unlocked = []
        for achievement in self.achievements:
            if not achievement.unlocked and achievement.condition_fn():
                achievement.unlocked = True
                achievement.unlock_time = self.game.turns
                newly_unlocked.append(achievement)

                # Apply any rewards
                if achievement.reward:
                    self.apply_reward(achievement.reward)

        return newly_unlocked

    def apply_reward(self, reward):
        """Apply a reward to the player"""
        if isinstance(reward, dict):
            if 'item' in reward:
                # Add an item to player inventory
                self.game.player.items[reward['item']] = reward.get('description', 'A special item')
            elif 'knowledge' in reward:
                # Increase knowledge in specific area
                area = reward['knowledge']
                amount = reward.get('amount', 1)
                if area in self.game.player.knowledge:
                    self.game.player.knowledge[area] = min(MAX_KNOWLEDGE, self.game.player.knowledge[area] + amount)

    def calculate_score(self):
        """Calculate player's score based on various factors"""
        score = 0

        # Points for exploration
        visited_rooms = len([r for r in self.game.game_map.rooms.values() if r.visited])
        score += visited_rooms * 10  # 10 points per room visited

        # Points for viruses found and quarantined
        score += len(self.game.player.found_viruses) * 50       # 50 points per virus found
        score += len(self.game.player.quarantined_viruses) * 100  # 100 points per virus quarantined

        # Points for knowledge gained
        knowledge_total = sum(self.game.player.knowledge.values())
        score += knowledge_total * 20  # 20 points per knowledge level

        # Bonus for efficiency (fewer turns)
        if self.game.victory:
            efficiency_bonus = max(0, 500 - (self.game.turns * 5))
            score += efficiency_bonus

        # Points for achievements
        score += sum(100 for a in self.achievements if a.unlocked)

        return score

    def get_progress_report(self):
        """Generate a detailed progress report for the player"""
        report = "PROGRESS REPORT\n"
        report += "===============\n\n"

        report += f"Exploration: {self.exploration_progress}% of system mapped\n"
        report += f"Knowledge: {self.knowledge_progress}% of total knowledge\n"
        report += f"Security: {self.virus_progress}% of virus threats handled\n\n"

        report += f"Current Score: {self.total_score} points\n\n"

        # List achievements
        if any(a.unlocked for a in self.achievements):
            report += "Achievements Unlocked:\n"
            for achievement in sorted([a for a in self.achievements if a.unlocked], key=lambda a: a.unlock_time):
                report += f"- {achievement.name}: {achievement.description}\n"

        # List locked achievements with hints
        locked = [a for a in self.achievements if not a.unlocked]
        if locked:
            report += "\nRemaining Challenges:\n"
            for achievement in locked:
                report += f"- ???: {achievement.description}\n"

        return report
