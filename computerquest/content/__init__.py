# ABOUTME: Static player-facing text (help, welcome, component articles).
# ABOUTME: Kept out of game.py so wording edits never touch game logic.

from computerquest.content.help import help_text
from computerquest.content.topics import COMPONENT_TOPICS, component_info
from computerquest.content.welcome import render_welcome

__all__ = ["COMPONENT_TOPICS", "component_info", "help_text", "render_welcome"]
