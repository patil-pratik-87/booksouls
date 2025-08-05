"""
Agents module for BookSouls character and author AI agents.
"""

from .base_agent import BaseAgent, AgentConfig
from .character_agent import CharacterAgent, CharacterPersona
from .character_extractor import CharacterExtractor
from .character_factory import CharacterFactory

# Note: AuthorAgent not yet implemented
# from .author_agent import AuthorAgent

__all__ = [
    "BaseAgent", 
    "AgentConfig",
    "CharacterAgent", 
    "CharacterPersona",
    "CharacterExtractor",
    "CharacterFactory"
]