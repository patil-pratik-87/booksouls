"""
Base agent class for BookSouls character and author agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from crewai import Agent
from langchain_openai import ChatOpenAI



@dataclass
class AgentConfig:
    """Configuration for BookSouls agents."""
    name: str
    role: str
    goal: str
    backstory: str
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 2000
    memory_window: int = 10


class BaseAgent(ABC):
    """Abstract base class for BookSouls agents."""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
            book_context: Context about the book/story world
        """
        self.config = config
        self.book_context = ''
        
        # Initialize language model
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        # Create CrewAI agent with memory enabled
        self.agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            memory=True
        )
    
    
    @abstractmethod
    def generate_system_prompt(self) -> str:
        """
        Generate the system prompt for this agent.
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def process_user_input(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Process user input and generate appropriate response.
        
        Args:
            user_input: User's message/question
            conversation_history: Previous conversation context
            
        Returns:
            Agent's response
        """
        pass
    
    
    
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": self.config.name,
            "role": self.config.role,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "memory_window": self.config.memory_window
        }
    
    def set_context(self, new_context: str) -> None:
        """
        Update the book context for this agent.
        
        Args:
            new_context: New book context information
        """
        self.book_context = new_context
    
    def validate_response(self, response: str) -> bool:
        """
        Validate that the agent's response is appropriate.
        
        Args:
            response: Generated response to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        if not response or len(response.strip()) == 0:
            return False
        
        # Check for meta-commentary that breaks character immersion
        meta_phrases = [
            "as an ai", "i am a language model", "i cannot", "as a fictional character",
            "this is a story", "in the book", "the author wrote"
        ]
        
        response_lower = response.lower()
        for phrase in meta_phrases:
            if phrase in response_lower:
                return False
        
        return True
    
    def enhance_response(self, response: str) -> str:
        """
        Enhance the response with character-specific formatting or additions.
        
        Args:
            response: Raw response from the agent
            
        Returns:
            Enhanced response
        """
        # Remove any meta-commentary
        if not self.validate_response(response):
            return self._generate_fallback_response()
        
        # Basic enhancement - can be overridden by subclasses
        return response.strip()
    
    def _generate_fallback_response(self) -> str:
        """
        Generate a fallback response when the main response is invalid.
        
        Returns:
            Fallback response string
        """
        return "I'm not sure how to respond to that right now. Could you ask me something else?"