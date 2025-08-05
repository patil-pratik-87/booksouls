"""
Tests for Character Agent functionality.

Basic tests to verify character agent creation, persona extraction,
and role-aware reasoning capabilities.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.character_agent import CharacterAgent, CharacterPersona
from src.agents.character_extractor import CharacterExtractor
from src.agents.character_factory import CharacterFactory
from src.agents.base_agent import AgentConfig


class TestCharacterPersona(unittest.TestCase):
    """Test CharacterPersona data class."""
    
    def setUp(self):
        """Set up test persona."""
        self.persona = CharacterPersona(
            name="Test Character",
            personality_traits=["brave", "intelligent", "stubborn"],
            motivations=["protect others", "seek truth"],
            speech_style={
                "formality": "formal",
                "emotional_tendency": "calm",
                "key_phrases": ["indeed", "I believe"]
            },
            core_beliefs=["honesty is important", "everyone deserves respect"],
            knowledge_base=["military tactics", "ancient history"],
            emotional_patterns={
                "default_state": "calm",
                "stress_response": "analytical"
            },
            relationships={"Friend": "ally", "Enemy": "adversary"},
            voice_characteristics={
                "vocabulary_level": "sophisticated",
                "dialogue_length": "moderate"
            },
            story_context="A knight from a medieval kingdom facing dark forces.",
            character_evolution=[]
        )
    
    def test_persona_creation(self):
        """Test persona object creation."""
        self.assertEqual(self.persona.name, "Test Character")
        self.assertIn("brave", self.persona.personality_traits)
        self.assertEqual(len(self.persona.motivations), 2)
        self.assertEqual(self.persona.speech_style["formality"], "formal")


class TestCharacterExtractor(unittest.TestCase):
    """Test CharacterExtractor functionality."""
    
    def setUp(self):
        """Set up mock indexer and extractor."""
        self.mock_indexer = Mock()
        self.extractor = CharacterExtractor(self.mock_indexer)
        
        # Mock character data
        self.mock_character_data = {
            'dialogues': [
                {
                    'document': 'Hello there, friend. How are you today?',
                    'metadata': {'character': 'TestChar', 'chapter': 1}
                }
            ],
            'profiles': [
                {
                    'document': 'Character profile for TestChar',
                    'metadata': {
                        'character': 'TestChar',
                        'chapter': 1,
                        'personality_traits': '["friendly", "helpful"]',
                        'motivations': '["help others"]',
                        'core_beliefs': '["kindness matters"]'
                    }
                }
            ],
            'narrative_context': [
                {
                    'document': 'TestChar was known throughout the kingdom for their kindness.',
                    'metadata': {'chapter': 1}
                }
            ],
            'thematic_context': []
        }
    
    def test_extractor_initialization(self):
        """Test extractor initialization."""
        self.assertEqual(self.extractor.indexer, self.mock_indexer)
        self.assertEqual(len(self.extractor._character_cache), 0)
    
    @patch.object(CharacterExtractor, '_gather_character_data')
    def test_extract_character_persona(self, mock_gather):
        """Test character persona extraction."""
        mock_gather.return_value = self.mock_character_data
        
        persona = self.extractor.extract_character_persona("TestChar")
        
        self.assertIsNotNone(persona)
        self.assertEqual(persona.name, "TestChar")
        self.assertIn("friendly", persona.personality_traits)
        self.assertIn("help others", persona.motivations)
    
    def test_safe_json_load(self):
        """Test safe JSON loading utility."""
        # Valid JSON
        result = self.extractor._safe_json_load('["test", "data"]')
        self.assertEqual(result, ["test", "data"])
        
        # Invalid JSON
        result = self.extractor._safe_json_load('invalid json', default=[])
        self.assertEqual(result, [])
    
    def test_cache_functionality(self):
        """Test character caching."""
        # Mock successful extraction
        with patch.object(self.extractor, '_gather_character_data') as mock_gather:
            mock_gather.return_value = self.mock_character_data
            
            # First extraction should call gather_character_data
            persona1 = self.extractor.extract_character_persona("TestChar")
            self.assertEqual(mock_gather.call_count, 1)
            
            # Second extraction should use cache
            persona2 = self.extractor.extract_character_persona("TestChar")
            self.assertEqual(mock_gather.call_count, 1)  # Still 1, not called again
            
            # Should be same object from cache
            self.assertEqual(id(persona1), id(persona2))


class TestCharacterAgent(unittest.TestCase):
    """Test CharacterAgent functionality."""
    
    def setUp(self):
        """Set up test agent."""
        self.mock_indexer = Mock()
        
        self.persona = CharacterPersona(
            name="Agent Test",
            personality_traits=["analytical", "direct"],
            motivations=["solve problems"],
            speech_style={"formality": "professional"},
            core_beliefs=["logic prevails"],
            knowledge_base=["science", "mathematics"],
            emotional_patterns={"default_state": "focused"},
            relationships={"Colleague": "peer"},
            voice_characteristics={"vocabulary_level": "technical"},
            story_context="A scientist in a research facility",
            character_evolution=[]
        )
        
        # Mock the CrewAI agent creation
        with patch('src.agents.base_agent.Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance
            
            self.agent = CharacterAgent(self.persona, self.mock_indexer)
            self.agent.agent.execute_task = Mock(return_value="Test response from character")
    
    def test_agent_initialization(self):
        """Test character agent initialization."""
        self.assertEqual(self.agent.persona.name, "Agent Test")
        self.assertEqual(self.agent.current_emotional_state, "neutral")
        self.assertIsNotNone(self.agent.config)
    
    def test_determine_context_type(self):
        """Test context type determination."""
        # Logical analysis scenario
        logical_input = "Analyze the problem and explain the solution"
        context_type = self.agent._determine_context_type(logical_input)
        self.assertEqual(context_type, "logical_analysis")
        
        # Vivid interaction scenario
        vivid_input = "Tell me about your feelings on this matter"
        context_type = self.agent._determine_context_type(vivid_input)
        self.assertEqual(context_type, "vivid_interaction")
    
    def test_generate_system_prompt(self):
        """Test system prompt generation."""
        prompt = self.agent.generate_system_prompt()
        
        self.assertIn("Agent Test", prompt)
        self.assertIn("analytical", prompt)
        self.assertIn("Role-Aware Reasoning", prompt)
        self.assertIn("scientist in a research facility", prompt)
    
    def test_emotional_response_generation(self):
        """Test emotional response generation."""
        # Happy input
        response = self.agent._generate_emotional_response("That's wonderful news!")
        self.assertIn("pleased", response.lower())
        
        # Question input
        response = self.agent._generate_emotional_response("What do you think about this?")
        self.assertIn("curious", response.lower())
    
    def test_response_validation(self):
        """Test response validation."""
        # Valid response
        self.assertTrue(self.agent.validate_response("This is a good response."))
        
        # Invalid responses (meta-commentary)
        self.assertFalse(self.agent.validate_response("As an AI, I cannot help you."))
        self.assertFalse(self.agent.validate_response("I am a language model"))
        
        # Empty response
        self.assertFalse(self.agent.validate_response(""))
    
    def test_character_info_retrieval(self):
        """Test character information retrieval."""
        info = self.agent.get_character_info()
        
        self.assertEqual(info['character_name'], "Agent Test")
        self.assertIn('personality_traits', info)
        self.assertIn('motivations', info)
        self.assertEqual(info['current_emotional_state'], "neutral")


class TestCharacterFactory(unittest.TestCase):
    """Test CharacterFactory functionality."""
    
    def setUp(self):
        """Set up mock components."""
        self.mock_indexer = Mock()
        self.factory = CharacterFactory(self.mock_indexer)
        
        # Mock extractor
        self.factory.extractor = Mock()
        self.mock_persona = CharacterPersona(
            name="Factory Test",
            personality_traits=["creative"],
            motivations=["build things"],
            speech_style={},
            core_beliefs=[],
            knowledge_base=[],
            emotional_patterns={},
            relationships={},
            voice_characteristics={"dialogue_length": "moderate"},
            story_context="A builder",
            character_evolution=[]
        )
        self.factory.extractor.extract_character_persona.return_value = self.mock_persona
    
    def test_factory_initialization(self):
        """Test factory initialization."""
        self.assertEqual(self.factory.indexer, self.mock_indexer)
        self.assertIsInstance(self.factory.extractor, Mock)
        self.assertEqual(len(self.factory._agent_cache), 0)
    
    @patch('src.agents.character_factory.CharacterAgent')
    def test_create_character_agent(self, mock_agent_class):
        """Test character agent creation."""
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance
        
        agent = self.factory.create_character_agent("Factory Test")
        
        self.assertIsNotNone(agent)
        self.factory.extractor.extract_character_persona.assert_called_once_with("Factory Test")
        mock_agent_class.assert_called_once()
    
    def test_character_config_creation(self):
        """Test character-specific config creation."""
        config = self.factory._create_character_config(self.mock_persona)
        
        self.assertIsInstance(config, AgentConfig)
        self.assertIn("Factory Test", config.name)
        self.assertEqual(config.max_tokens, 2000)  # Default for moderate dialogue length
    


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)