#!/usr/bin/env python3
"""
Unit tests for the progress tracking system
"""

import unittest
from unittest.mock import patch, MagicMock
from computerquest.mechanics.progress import Achievement, ProgressSystem
from computerquest.config import VIRUS_TYPES, MAX_KNOWLEDGE

class TestAchievement(unittest.TestCase):
    """Test cases for the Achievement class"""
    
    def test_init(self):
        """Test achievement initialization"""
        # Create a condition function
        condition = lambda: True
        
        # Create achievement
        achievement = Achievement(
            id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            condition_fn=condition,
            reward={"item": "trophy", "description": "A shiny trophy"}
        )
        
        # Check attributes
        self.assertEqual(achievement.id, "test_achievement")
        self.assertEqual(achievement.name, "Test Achievement")
        self.assertEqual(achievement.description, "A test achievement")
        self.assertEqual(achievement.condition_fn, condition)
        self.assertFalse(achievement.unlocked)
        self.assertIsNone(achievement.unlock_time)
        self.assertEqual(achievement.reward, {"item": "trophy", "description": "A shiny trophy"})

class TestProgressSystem(unittest.TestCase):
    """Test cases for the ProgressSystem class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock game
        self.game = MagicMock()
        
        # Mock player
        self.game.player = MagicMock()
        self.game.player.found_viruses = []
        self.game.player.quarantined_viruses = []
        self.game.player.knowledge = {
            "cpu": 0,
            "memory": 0,
            "storage": 0,
            "networking": 0,
            "security": 0
        }
        
        # Mock game map
        self.game.game_map = MagicMock()
        self.room1 = MagicMock()
        self.room1.visited = True
        self.room2 = MagicMock()
        self.room2.visited = False
        self.room3 = MagicMock()
        self.room3.visited = False
        
        self.game.game_map.rooms = {
            "room1": self.room1,
            "room2": self.room2,
            "room3": self.room3
        }
        
        # Mock turns and victory
        self.game.turns = 10
        self.game.victory = False
        
        # Create progress system
        self.progress = ProgressSystem(self.game)
    
    def test_init(self):
        """Test progress system initialization"""
        # Check basic properties
        self.assertEqual(self.progress.game, self.game)
        self.assertEqual(self.progress.exploration_progress, 0)
        self.assertEqual(self.progress.knowledge_progress, 0)
        self.assertEqual(self.progress.virus_progress, 0)
        self.assertEqual(self.progress.total_score, 0)
        
        # Check achievements were created
        self.assertGreater(len(self.progress.achievements), 0)
        
        # Check achievement types
        achievement_ids = [a.id for a in self.progress.achievements]
        self.assertIn("first_step", achievement_ids)
        self.assertIn("explorer", achievement_ids)
        self.assertIn("first_virus", achievement_ids)
        self.assertIn("virus_hunter", achievement_ids)
        self.assertIn("system_savior", achievement_ids)
        self.assertIn("cpu_expert", achievement_ids)
        self.assertIn("computer_scientist", achievement_ids)
        self.assertIn("efficient", achievement_ids)
    
    def test_update_exploration_progress(self):
        """Test updating exploration progress"""
        # Initial state: 1 out of 3 rooms visited (33%)
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.exploration_progress, 33)
        
        # Mark another room as visited (66%)
        self.room2.visited = True
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.exploration_progress, 66)
        
        # Mark all rooms as visited (100%)
        self.room3.visited = True
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.exploration_progress, 100)
    
    def test_update_knowledge_progress(self):
        """Test updating knowledge progress"""
        # Initial state: 0 knowledge (0%)
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.knowledge_progress, 0)
        
        # Set some knowledge values
        self.game.player.knowledge = {
            "cpu": 2,
            "memory": 1,
            "storage": 0,
            "networking": 0,
            "security": 2
        }
        
        # Max knowledge: 5 areas * MAX_KNOWLEDGE (5) = 25
        # Current knowledge: 5, so 20%
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.knowledge_progress, 20)
        
        # Set all knowledge to maximum
        self.game.player.knowledge = {
            "cpu": MAX_KNOWLEDGE,
            "memory": MAX_KNOWLEDGE,
            "storage": MAX_KNOWLEDGE,
            "networking": MAX_KNOWLEDGE,
            "security": MAX_KNOWLEDGE
        }
        
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.knowledge_progress, 100)
    
    def test_update_virus_progress(self):
        """Test updating virus progress"""
        # Initial state: 0 viruses found/quarantined (0%)
        newly_unlocked = self.progress.update()
        self.assertEqual(self.progress.virus_progress, 0)
        
        # Find 2 out of 5 viruses (20% - finds are 50% of progress)
        self.game.player.found_viruses = VIRUS_TYPES[:2]  # First 2 viruses
        newly_unlocked = self.progress.update()
        
        # 2/5 * 50% = 20%
        self.assertEqual(self.progress.virus_progress, 20)
        
        # Quarantine 1 virus (found 2, quarantined 1: 20% + 10% = 30%)
        self.game.player.quarantined_viruses = [VIRUS_TYPES[0]]  # First virus
        newly_unlocked = self.progress.update()
        
        # 2/5 * 50% + 1/5 * 50% = 30%
        self.assertEqual(self.progress.virus_progress, 30)
        
        # Find and quarantine all viruses (100%)
        self.game.player.found_viruses = VIRUS_TYPES.copy()
        self.game.player.quarantined_viruses = VIRUS_TYPES.copy()
        newly_unlocked = self.progress.update()
        
        # 5/5 * 50% + 5/5 * 50% = 100%
        self.assertEqual(self.progress.virus_progress, 100)
    
    def test_achievement_unlocking(self):
        """Test unlocking achievements"""
        # Test first_step achievement (visit > 1 room)
        self.room2.visited = True  # Now 2 rooms visited
        newly_unlocked = self.progress.update()
        
        # Check first_step was unlocked
        first_step = next((a for a in newly_unlocked if a.id == "first_step"), None)
        self.assertIsNotNone(first_step)
        self.assertTrue(first_step.unlocked)
        self.assertEqual(first_step.unlock_time, self.game.turns)
        
        # Test virus hunter achievement (find all viruses)
        self.game.player.found_viruses = VIRUS_TYPES.copy()
        newly_unlocked = self.progress.update()
        
        # Check virus_hunter was unlocked
        virus_hunter = next((a for a in newly_unlocked if a.id == "virus_hunter"), None)
        self.assertIsNotNone(virus_hunter)
        
        # Test system_savior achievement (quarantine all viruses)
        self.game.player.quarantined_viruses = VIRUS_TYPES.copy()
        newly_unlocked = self.progress.update()
        
        # Check system_savior was unlocked
        system_savior = next((a for a in newly_unlocked if a.id == "system_savior"), None)
        self.assertIsNotNone(system_savior)
        
        # Test efficient achievement (complete in under 50 turns)
        self.game.victory = True  # Game completed
        newly_unlocked = self.progress.update()
        
        # Check efficient was unlocked
        efficient = next((a for a in newly_unlocked if a.id == "efficient"), None)
        self.assertIsNotNone(efficient)
    
    def test_apply_reward(self):
        """Test applying achievement rewards"""
        # Test item reward
        item_reward = {"item": "trophy", "description": "A shiny trophy"}
        self.progress.apply_reward(item_reward)
        
        # Check item was added to player inventory
        self.game.player.items.__setitem__.assert_called_with("trophy", "A shiny trophy")
        
        # Test knowledge reward
        knowledge_reward = {"knowledge": "cpu", "amount": 2}
        
        # Set initial knowledge
        self.game.player.knowledge = {"cpu": 1, "memory": 0, "storage": 0, "networking": 0, "security": 0}
        
        self.progress.apply_reward(knowledge_reward)
        
        # Check knowledge was increased
        self.assertEqual(self.game.player.knowledge["cpu"], 3)
        
        # Test knowledge reward at max
        self.game.player.knowledge = {"cpu": MAX_KNOWLEDGE - 1, "memory": 0, "storage": 0, "networking": 0, "security": 0}
        
        self.progress.apply_reward(knowledge_reward)
        
        # Check knowledge was capped at MAX_KNOWLEDGE
        self.assertEqual(self.game.player.knowledge["cpu"], MAX_KNOWLEDGE)
    
    def test_calculate_score(self):
        """Test score calculation"""
        # Set up test conditions
        
        # 2 out of 3 rooms visited
        self.room2.visited = True
        
        # 2 viruses found, 1 quarantined
        self.game.player.found_viruses = VIRUS_TYPES[:2]
        self.game.player.quarantined_viruses = [VIRUS_TYPES[0]]
        
        # Some knowledge gained
        self.game.player.knowledge = {
            "cpu": 3,
            "memory": 2,
            "storage": 1,
            "networking": 0,
            "security": 4
        }
        
        # 3 achievements unlocked
        for achievement in self.progress.achievements[:3]:
            achievement.unlocked = True
        
        # Calculate score
        self.progress.update()  # Update metrics first
        score = self.progress.calculate_score()

        # Expected components:
        # - 2 rooms visited: 2 * 10 = 20
        # - 2 viruses found: 2 * 50 = 100
        # - 1 virus quarantined: 1 * 100 = 100
        # - Knowledge total (3+2+1+0+4) = 10: 10 * 20 = 200
        # - Achievements: 3 manual + 2 auto-unlocked by update()
        #   (first_virus on found>=1, first_quarantine on quarantined>=1)
        #   = 5 * 100 = 500
        # - No efficiency bonus (not victorious)
        # Total: 20 + 100 + 100 + 200 + 500 = 920
        self.assertEqual(score, 920)

        # Test with efficiency bonus (calculate_score does not re-evaluate
        # achievements, so the 5 unlocked above remain)
        self.game.victory = True
        self.game.turns = 10
        score_with_bonus = self.progress.calculate_score()
        efficiency_bonus = 500 - (10 * 5)  # 450
        self.assertEqual(score_with_bonus, 920 + efficiency_bonus)
    
    def test_get_progress_report(self):
        """Test progress report generation"""
        # Set up some progress
        self.progress.exploration_progress = 67
        self.progress.knowledge_progress = 42
        self.progress.virus_progress = 30
        self.progress.total_score = 850
        
        # Unlock some achievements
        for i, achievement in enumerate(self.progress.achievements[:3]):
            achievement.unlocked = True
            achievement.unlock_time = i * 10  # Different unlock times
        
        # Get report
        report = self.progress.get_progress_report()
        
        # Check contents
        self.assertIn("PROGRESS REPORT", report)
        self.assertIn("Exploration: 67%", report)
        self.assertIn("Knowledge: 42%", report)
        self.assertIn("Security: 30%", report)
        self.assertIn("Current Score: 850", report)
        
        # Check unlocked achievements section
        self.assertIn("Achievements Unlocked:", report)
        
        # Check locked achievements section
        self.assertIn("Remaining Challenges:", report)
        self.assertIn("???:", report)  # Hidden achievement names

if __name__ == "__main__":
    unittest.main()