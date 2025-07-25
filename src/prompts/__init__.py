"""
Prompts module for BookSouls project.
Contains prompt templates for various AI tasks.
"""

from .dialogue_extraction_prompts import BASIC_DIALOGUE_EXTRACTION, ADVANCED_DIALOGUE_EXTRACTION
from .character_analysis_prompts import CHARACTER_ANALYSIS_PROMPT, CHARACTER_ANALYSIS_ENHANCED_PROMPT, format_character_data_section

__all__ = [
    'BASIC_DIALOGUE_EXTRACTION',
    'ADVANCED_DIALOGUE_EXTRACTION',
    'CHARACTER_ANALYSIS_PROMPT',
    'CHARACTER_ANALYSIS_ENHANCED_PROMPT',
    'format_character_data_section'
]