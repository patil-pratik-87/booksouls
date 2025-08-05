"""
Character Factory - Creates and manages CrewAI character agents dynamically.

Factory pattern for creating character agents with full personas extracted
from the vector store. Manages agent lifecycle and provides easy access.
"""

from typing import Dict, List, Optional, Any
import os
from crewai import Crew, Task

from .character_agent import CharacterAgent, CharacterPersona
from .character_extractor import CharacterExtractor
from .base_agent import AgentConfig
from ..indexers.dual_vector_indexer import DualVectorIndexer


class CharacterFactory:
    """
    Factory for creating and managing character agents.
    
    Provides centralized creation and management of character agents
    with full persona extraction from the vector store.
    """
    
    def __init__(self, indexer: DualVectorIndexer):
        """
        Initialize factory with indexer access.
        
        Args:
            indexer: DualVectorIndexer for character data retrieval
        """
        self.indexer = indexer
        self.extractor = CharacterExtractor(indexer)
    
    def create_character_agent(
        self, 
        character_name: str, 
        config: Optional[AgentConfig] = None
    ) -> Optional[CharacterAgent]:
        """
        Create a character agent with full persona.
        
        Args:
            character_name: Name of character to create agent for
            config: Optional custom configuration
            
        Returns:
            CharacterAgent instance or None if character not found
        """
        # Extract character persona
        persona = self.extractor.extract_character_persona(character_name)
        
        if not persona:
            print(f"Could not extract persona for character: {character_name}")
            return None
        
        # Create character-specific config if none provided
        if config is None:
            config = self._create_character_config(persona)
        
        # Create character agent
        try:
            agent = CharacterAgent(persona, self.indexer, config)
            return agent
            
        except Exception as e:
            print(f"Error creating character agent for {character_name}: {str(e)}")
            return None
    
    def _create_character_config(self, persona: CharacterPersona) -> AgentConfig:
        """Create optimized config for character agent."""
        
        
        return AgentConfig(
            name=f"{persona.name}_Character_Agent",
            role=f"Character embodiment of {persona.name}",
            goal=f"Authentically represent {persona.name} with their unique personality, speech patterns, and knowledge",
            backstory=f"I am {persona.name}.",
            temperature=0.7,
            memory_window=15  # Longer memory for character consistency
        )
    
    def get_character_agent(self, character_name: str) -> Optional[CharacterAgent]:
        """Create a character agent."""
        return self.create_character_agent(character_name)
    
    def get_available_characters(self) -> List[str]:
        """Get list of available characters from the extractor."""
        return self.extractor.get_available_characters()
    
    def create_character_crew(
        self, 
        characters: List[str], 
        scenario_description: str = "Character interaction scenario"
    ) -> Optional[Crew]:
        """
        Create a CrewAI crew with multiple character agents.
        
        Args:
            characters: List of character names to include
            scenario_description: Description of the scenario/task
            
        Returns:
            Crew instance or None if creation fails
        """
        # Create agents for all characters
        agents = []
        for char_name in characters:
            agent = self.get_character_agent(char_name)
            if agent:
                agents.append(agent.agent)  # Get the CrewAI agent
            else:
                print(f"Warning: Could not create agent for {char_name}")
        
        if not agents:
            print("No valid agents created for crew")
            return None
        
        # Create a basic interaction task
        task = Task(
            description=f"""
            {scenario_description}
            
            Each character should respond authentically based on their personality,
            knowledge, and relationships. Maintain character consistency throughout
            the interaction while advancing the conversation naturally.
            """,
            agent=agents[0],  # Primary agent
            expected_output="Authentic character responses that maintain personality consistency"
        )
        
        # Create crew
        crew = Crew(
            agents=agents,
            tasks=[task],
            verbose=True,
            process="sequential"  # Characters take turns
        )
        
        return crew
    
    def execute_character_conversation(
        self, 
        characters: List[str], 
        prompt: str,
        max_rounds: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a multi-character conversation.
        
        Args:
            characters: List of character names
            prompt: Initial conversation prompt
            max_rounds: Maximum conversation rounds
            
        Returns:
            Conversation results with character responses
        """
        results = {
            'characters': characters,
            'prompt': prompt,
            'conversation': [],
            'success': False
        }
        
        # Get character agents
        agents = {}
        for char_name in characters:
            agent = self.get_character_agent(char_name)
            if agent:
                agents[char_name] = agent
        
        if not agents:
            results['error'] = "No valid character agents available"
            return results
        
        try:
            # Execute conversation rounds
            current_prompt = prompt
            conversation_history = []
            
            for round_num in range(max_rounds):
                round_responses = {}
                
                for char_name, agent in agents.items():
                    # Build conversation context
                    context_history = [
                        {'role': 'system', 'content': f'Conversation round {round_num + 1}'},
                        {'role': 'user', 'content': current_prompt}
                    ]
                    
                    # Add previous responses from other characters
                    for prev_char, prev_response in round_responses.items():
                        context_history.append({
                            'role': 'assistant', 
                            'content': f"{prev_char}: {prev_response}"
                        })
                    
                    # Generate character response
                    response = agent.process_user_input(current_prompt, context_history)
                    round_responses[char_name] = response
                
                # Add round to conversation
                conversation_history.append({
                    'round': round_num + 1,
                    'responses': round_responses
                })
                
                # Update prompt for next round (use last character's response)
                if round_responses:
                    last_response = list(round_responses.values())[-1]
                    current_prompt = f"Continuing from: {last_response}"
            
            results['conversation'] = conversation_history
            results['success'] = True
            
        except Exception as e:
            results['error'] = f"Conversation execution failed: {str(e)}"
        
        return results
    
    def chat_with_character(
        self, 
        character_name: str, 
        message: str,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Simple chat interface with a single character.
        
        Args:
            character_name: Name of character to chat with
            message: User's message
            conversation_history: Previous conversation history
            
        Returns:
            Chat response with character info
        """
        agent = self.get_character_agent(character_name)
        
        if not agent:
            return {
                'success': False,
                'error': f"Character '{character_name}' not available",
                'available_characters': self.get_available_characters()
            }
        
        try:
            # Generate response
            response = agent.process_user_input(message, conversation_history)
            
            return {
                'success': True,
                'character': character_name,
                'message': message,
                'response': response,
                'character_info': {
                    'personality_traits': agent.persona.personality_traits,
                    'current_emotional_state': agent.current_emotional_state,
                    'relationships': list(agent.persona.relationships.keys())
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating response: {str(e)}",
                'character': character_name
            }
    
    def get_character_info(self, character_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed character information."""
        agent = self.get_character_agent(character_name)
        
        if not agent:
            return None
        
        return {
            'name': character_name,
            'persona': {
                'personality_traits': agent.persona.personality_traits,
                'motivations': agent.persona.motivations,
                # 'core_beliefs': agent.persona.core_beliefs,
                'speech_style': agent.persona.speech_style,
                'relationships': agent.persona.relationships,
                # 'story_context': agent.persona.story_context
            },
            'agent_info': agent.get_character_info(),
            'evolution': [
                {
                    'chapter': profile.chapter,
                    'traits': profile.personality_traits,
                    'emotional_state': profile.emotional_state
                }
                for profile in agent.persona.character_evolution
            ]
        }
    
    
    
    
    
    def create_character_comparison(self, char1: str, char2: str) -> Dict[str, Any]:
        """Create a comparison between two characters."""
        agent1 = self.get_character_agent(char1)
        agent2 = self.get_character_agent(char2)
        
        if not agent1 or not agent2:
            return {
                'success': False,
                'error': 'One or both characters not available'
            }
        
        return {
            'success': True,
            'characters': [char1, char2],
            'comparison': {
                'personality_traits': {
                    char1: agent1.persona.personality_traits,
                    char2: agent2.persona.personality_traits
                },
                'motivations': {
                    char1: agent1.persona.motivations,
                    char2: agent2.persona.motivations
                },
                'speech_styles': {
                    char1: agent1.persona.speech_style,
                    char2: agent2.persona.speech_style
                },
                'relationships': {
                    char1: agent1.persona.relationships,
                    char2: agent2.persona.relationships
                },
                'shared_relationships': list(
                    set(agent1.persona.relationships.keys()) & 
                    set(agent2.persona.relationships.keys())
                )
            }
        }