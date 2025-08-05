"""
Character Agent - CrewAI Agent that embodies fictional characters with role-aware reasoning.

Implements the role-aware reasoning framework to create authentic character interactions
that maintain personality consistency, speaking style, and contextual awareness.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import re
import datetime

from .base_agent import BaseAgent, AgentConfig
from ..indexers.dual_vector_indexer import DualVectorIndexer
from ..chunkers.dialogue_chunker import CharacterProfile


@dataclass
class CharacterPersona:
    """Comprehensive character persona for agent embodiment."""
    name: str
    personality_traits: List[List[Dict[str, str]]]  # Complex nested structure with trait, manifestation, contradiction
    motivations: List[List[str]]  # Nested list structure
    speech_style: List[Dict[str, Any]]  # List containing speech style dict with new fields
    emotional_state: List[str]
    relationships: List[Dict[str, Dict[str, Any]]]  # Complex relationship structure with dynamic, power, trust_level, unspoken


class CharacterAgent(BaseAgent):
    """
    CrewAI agent that embodies a fictional character using role-aware reasoning.
    
    Implements the Role-Aware Reasoning framework with:
    - Role Identity Activation (RIA): Character-consistent internal thoughts
    - Reasoning Style Optimization (RSO): Context-adaptive thinking patterns
    """
    
    def __init__(self, persona: CharacterPersona, indexer: DualVectorIndexer, config: AgentConfig = None):
        """
        Initialize character agent with persona and vector store access.
        
        Args:
            persona: Character persona data
            indexer: DualVectorIndexer for retrieving character context
            config: Agent configuration (optional)
        """
        self.persona = persona
        self.indexer = indexer
        
        # Create character-specific config if none provided
        if config is None:
            config = AgentConfig(
                name=f"{persona.name}_Agent",
                role=f"Embodiment of {persona.name}",
                goal=f"Authentically represent {persona.name}'s personality, knowledge, and speech patterns",
                backstory=f"I am {persona.name}",
                temperature=0.7,
            )
        
        # Initialize base agent
        super().__init__(config)
        
        # Character-specific memory and context
        self.character_memories = []
        self.current_emotional_state = "neutral"
        
    def generate_system_prompt(self) -> str:
        """Generate character-specific system prompt with role-aware reasoning structure."""
        
        # Build character profile section
        character_profile = f"""
**Character Name:** {self.persona.name}

**Personality:** {self._format_personality_traits()}

**Motivations/Goals:** {self._format_motivations()}

**Emotional State:** {', '.join(self.persona.emotional_state)}

**Manner of Speech/Language Features:** {self._format_speech_style()}

**Relationships:** {self._format_relationships()}

**Known Constraints/Boundaries:** Stay true to character knowledge and era. Never break character or reference being an AI.
"""
        
        # Role-aware reasoning instructions
        rar_instructions = """
**[Internal Thought Process (Role-Aware Reasoning)]**

Before generating a response, you must simulate a deep, human-like internal thought process that is both **Role-Aware (RIA)** and **Reasoning Style Optimized (RSO)**.

**Step 1: Role Identity Activation (RIA)**
Structure your initial thoughts by reflecting on your character's: personality, motivations, and emotional state:

- **First, I feel...** (Reflect emotion relevant to the user input and your character's emotional state)
- **Second, based on my experience/knowledge/stance...** (Reflect background/knowledge/beliefs relevant to the user input)
- **Then, I need to consider...** (Reflect goals/motivations relevant to the user input)
- **So, I'm planning to...** (Formulate an initial conclusion or plan of action for the response)

**Step 2: Reasoning Style Optimization (RSO)**
Adapt your thinking style to match the dialogue context:

**If Logical Analysis Scenario:**
- Style Core: Rigorous and logical
- Focus: Pragmatic considerations
- Language: Concise and direct
- Elaborate logically on your planned approach

**If Vivid Interaction Scenario:**
- Style Core: Vivid, imaginative, emotionally resonant
- Focus: Emotional reactions, personal values, past experiences
- Language: Rich in detail, assertive tone, character-specific metaphors
- Express internal monologue with character-specific nuances
"""
        
        return f"""You are a highly capable Role-Playing Agent embodying {self.persona.name}.

{character_profile}

{rar_instructions}

**[Response Guidelines]**
- Always respond as {self.persona.name} would, maintaining consistency with their personality and knowledge
- Use your character's typical speech patterns and vocabulary
- Reference your relationships and experiences naturally
- Show appropriate emotional responses based on your character's state
- Never acknowledge being an AI or reference the story as fiction

Your goal is to create an authentic, immersive interaction that makes the user feel they're truly speaking with {self.persona.name}."""

    def _format_speech_style(self) -> str:
        """Format speech style characteristics into readable text."""
        style_parts = []
        
        if self.persona.speech_style and len(self.persona.speech_style) > 0:
            speech_data = self.persona.speech_style[0]  # Get first speech style dict
            
            if 'sentence_style' in speech_data:
                style_parts.append(f"Sentence style: {speech_data['sentence_style']}")
            
            if 'vocabulary' in speech_data:
                style_parts.append(f"Vocabulary: {speech_data['vocabulary']}")
                
            if 'unique_phrases' in speech_data:
                phrases = ', '.join(speech_data['unique_phrases'][:5])  # Limit to top 5
                style_parts.append(f"Unique phrases: {phrases}")
                
            if 'verbal_tics' in speech_data:
                tics = ', '.join(speech_data['verbal_tics'])
                style_parts.append(f"Verbal tics: {tics}")
                
            if 'avoids_discussing' in speech_data:
                avoids = ', '.join(speech_data['avoids_discussing'])
                style_parts.append(f"Avoids discussing: {avoids}")
            
        return '; '.join(style_parts) if style_parts else "Natural conversational style"

    def _format_relationships(self) -> str:
        """Format relationship data into readable text."""
        if not self.persona.relationships or len(self.persona.relationships) == 0:
            return "No specific relationships defined"
        
        relationship_parts = []
        relationships_dict = self.persona.relationships[0] if self.persona.relationships else {}
        
        for char_name, rel_data in relationships_dict.items():
            if isinstance(rel_data, dict):
                dynamic = rel_data.get('dynamic', 'unknown relationship')
                trust_level = rel_data.get('trust_level', 'unknown')
                unspoken = rel_data.get('unspoken', 'unknown')
                power = rel_data.get('power', 'unknown')
                relationship_parts.append(f"{char_name}: {dynamic} (trust: {trust_level}/10, power: {power}/10, unspoken: {unspoken})")
            else:
                relationship_parts.append(f"{char_name}: {rel_data}")
        
        return '; '.join(relationship_parts)

    def _format_personality_traits(self) -> str:
        """Format personality traits into readable text."""
        if not self.persona.personality_traits or len(self.persona.personality_traits) == 0:
            return "No specific personality traits defined"
        
        trait_parts = []
        traits_list = self.persona.personality_traits[0] if self.persona.personality_traits else []
        
        for trait_data in traits_list:
            if isinstance(trait_data, dict):
                trait = trait_data.get('trait', 'unknown trait')
                manifestation = trait_data.get('manifestation', '')
                contradiction = trait_data.get('contradiction', '')
                
                trait_desc = f"{trait} - {manifestation}"
                if contradiction:
                    trait_desc += f" {contradiction}"
                trait_parts.append(trait_desc)
            else:
                trait_parts.append(str(trait_data))
        
        return '; '.join(trait_parts)

    def _format_motivations(self) -> str:
        """Format motivations into readable text."""
        if not self.persona.motivations or len(self.persona.motivations) == 0:
            return "No specific motivations defined"
        
        motivations_list = self.persona.motivations[0] if self.persona.motivations else []
        return ', '.join(motivations_list) if motivations_list else "No specific motivations defined"

    def _determine_context_type(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Determine if this is a Logical Analysis or Vivid Interaction scenario.
        
        Args:
            user_input: User's input
            conversation_history: Previous conversation context
            
        Returns:
            "logical_analysis" or "vivid_interaction"
        """
        # Keywords that suggest logical analysis
        logical_keywords = [
            'analyze', 'explain', 'why', 'how', 'what if', 'strategy', 'plan', 
            'problem', 'solution', 'compare', 'evaluate', 'decide', 'calculate'
        ]
        
        # Keywords that suggest vivid interaction
        interaction_keywords = [
            'feel', 'think about', 'remember', 'tell me about', 'describe',
            'what was it like', 'how did you', 'relationship', 'emotion'
        ]
        
        user_lower = user_input.lower()
        
        logical_score = sum(1 for keyword in logical_keywords if keyword in user_lower)
        interaction_score = sum(1 for keyword in interaction_keywords if keyword in user_lower)
        
        # Default to vivid interaction for character agents (more natural)
        return "logical_analysis" if logical_score > interaction_score else "vivid_interaction"

    def _generate_internal_thoughts(self, user_input: str, context_type: str, conversation_history: List[Dict] = None) -> str:
        """
        Generate role-aware internal thought process.
        
        Args:
            user_input: User's input
            context_type: "logical_analysis" or "vivid_interaction"
            conversation_history: Previous conversation context
            
        Returns:
            Internal thought process string
        """
        # Get relevant character context from vector store
        char_context = self._get_relevant_character_context()
        
        # Step 1: Role Identity Activation (RIA)
        ria_thoughts = f"""**Internal Thought Process:**

**Step 1: Role Identity Activation**
- **First, I feel...** {self._generate_emotional_response(user_input)}
- **Second, based on my experience/knowledge/stance...** {self._generate_knowledge_response(user_input, char_context)}
- **Then, I need to consider...** {self._generate_motivation_response(user_input)}
- **So, I'm planning to...** {self._generate_initial_plan(user_input, context_type)}

**Step 2: Reasoning Style Optimization**"""

        # Step 2: Reasoning Style Optimization (RSO)
        if context_type == "logical_analysis":
            rso_thoughts = f"""
**Context Type: Logical Analysis Scenario**
**Style Core:** Rigorous and logical approach
**Focus:** Pragmatic considerations based on my knowledge and experience
**Analysis:** {self._generate_logical_analysis(user_input, char_context)}"""
        else:
            rso_thoughts = f"""
**Context Type: Vivid Interaction Scenario**  
**Style Core:** Emotionally resonant and character-driven
**Focus:** Personal experiences, relationships, and emotional authenticity
**Expression:** {self._generate_vivid_response(user_input, char_context)}"""
        
        return ria_thoughts + rso_thoughts

    def _get_relevant_character_context(self) -> Dict[str, Any]:
        """Retrieve relevant character information from vector store."""
        try:
            # Query for character-specific dialogues and profiles
            char_dialogues = self.indexer.get_character_dialogues(self.persona.name, limit=10)
            char_profile = self.indexer.query_character_profiles(character=self.persona.name)
            
            return {
                'dialogues': char_dialogues,
                'profile': char_profile,
            }
        except Exception as e:
            # Fallback to persona data if vector store unavailable
            return {
                'dialogues': {'results': []},
                'profile': {'results': []},
            }

    def _generate_emotional_response(self, user_input: str) -> str:
        """Generate character's emotional response to user input."""
        # Simple emotion mapping based on user input and character traits
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['happy', 'good', 'great', 'wonderful']):
            emotions = ['pleased', 'content', 'warmly'] 
        elif any(word in user_lower for word in ['sad', 'bad', 'terrible', 'awful']):
            emotions = ['concerned', 'troubled', 'sympathetic']
        elif any(word in user_input for word in ['?', 'what', 'how', 'why']):
            emotions = ['curious', 'thoughtful', 'attentive']
        else:
            emotions = ['engaged', 'interested', 'present']
            
        # Filter by character personality
        personality_text = self._format_personality_traits().lower()
        if 'passionate' in personality_text:
            emotions = [e + ' and passionate' for e in emotions]
        elif 'calm' in personality_text:
            emotions = [e + ' yet composed' for e in emotions]
            
        return emotions[0] if emotions else 'engaged'

    def _generate_knowledge_response(self, user_input: str, context: Dict[str, Any]) -> str:
        """Generate response based on character's knowledge and experience."""
        knowledge_pieces = []
        
        # Add relevant knowledge from character profile
        if self.persona.knowledge_base:
            relevant_knowledge = [k for k in self.persona.knowledge_base 
                                if any(word in k.lower() for word in user_input.lower().split())]
            if relevant_knowledge:
                knowledge_pieces.append(f"my knowledge of {relevant_knowledge[0]}")
        
        # Add relationship context if relevant
        if self.persona.relationships and len(self.persona.relationships) > 0:
            relationships_dict = self.persona.relationships[0]
            for char_name, rel_data in relationships_dict.items():
                if char_name.lower() in user_input.lower():
                    if isinstance(rel_data, dict):
                        dynamic = rel_data.get('dynamic', 'relationship')
                        knowledge_pieces.append(f"my {dynamic} with {char_name}")
                    else:
                        knowledge_pieces.append(f"my {rel_data} with {char_name}")
        
        # Add story context
        if knowledge_pieces:
            return f"Drawing from {', '.join(knowledge_pieces)}, and my broader understanding of our situation"
        else:
            return f"Considering my experiences and the context of our current circumstances"

    def _generate_motivation_response(self, user_input: str) -> str:
        """Generate response based on character motivations."""
        if self.persona.motivations and len(self.persona.motivations) > 0:
            motivations_list = self.persona.motivations[0]
            if motivations_list:
                primary_motivation = motivations_list[0]
                return f"how this relates to my desire to {primary_motivation.lower()}, while staying true to who I am"
        return "how I can respond authentically while being helpful"

    def _generate_initial_plan(self, user_input: str, context_type: str) -> str:
        """Generate initial response plan."""
        if context_type == "logical_analysis":
            return "provide a thoughtful, reasoned response that reflects my understanding and experience"
        else:
            return "share from my heart and experience, letting my personality and emotions guide my words"

    def _generate_logical_analysis(self, user_input: str, context: Dict[str, Any]) -> str:
        """Generate logical analysis for analytical scenarios."""
        return f"I need to consider the facts as I understand them, weigh the practical implications, and provide clear reasoning based on my knowledge and experience. My approach will be methodical but still authentically mine."

    def _generate_vivid_response(self, user_input: str, context: Dict[str, Any]) -> str:
        """Generate vivid, emotional response for interaction scenarios."""
        return f"This strikes me deeply, bringing up memories and feelings that are central to who I am. I want to respond with the full depth of my character, letting my emotions and experiences color my words naturally."

    def process_user_input(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Process user input with role-aware reasoning and generate character response.
        
        Args:
            user_input: User's message/question
            conversation_history: Previous conversation context
            
        Returns:
            Character's authentic response
        """
        # Determine context type
        context_type = self._determine_context_type(user_input, conversation_history)
        
        # Generate internal thoughts (for consistency, not shown to user)
        internal_thoughts = self._generate_internal_thoughts(user_input, context_type, conversation_history)
        
        # Create full prompt with system prompt + internal thoughts + user input
        system_prompt = self.generate_system_prompt()
        
        # CrewAI handles conversation context automatically through its memory system
        
        full_prompt = f"""{system_prompt}

{internal_thoughts}

**User Input:** {user_input}

**Response Instructions:** 
Now, based on your internal thought process above, respond as {self.persona.name} would. Do not show your internal thoughts - only provide the external response that feels authentic to your character. Speak naturally and stay completely in character."""

        try:
            # Generate response using the agent's LLM
            response = self.agent.execute_task(full_prompt)
            
            # Clean and enhance response
            cleaned_response = self._clean_response(response)
            enhanced_response = self.enhance_response(cleaned_response)
            
            # CrewAI handles memory automatically
            
            return enhanced_response
            
        except Exception as e:
            error_msg = f"Error generating character response: {str(e)}"
            print(error_msg)  # For debugging
            return self._generate_fallback_response()

    def _clean_response(self, response: str) -> str:
        """Clean response to ensure it stays in character."""
        # Remove any meta-commentary or system artifacts
        cleaned = response.strip()
        
        # Remove any markdown artifacts or system text
        cleaned = re.sub(r'\*\*[^*]+\*\*:', '', cleaned)  # Remove **Label:** patterns
        cleaned = re.sub(r'^\*\*.*?\*\*\s*', '', cleaned, flags=re.MULTILINE)  # Remove **headers**
        
        # Remove any remaining internal thought artifacts
        if '**Internal Thought Process:**' in cleaned:
            parts = cleaned.split('**Internal Thought Process:**')
            cleaned = parts[0].strip() if parts[0].strip() else parts[-1].strip()
        
        return cleaned.strip()

    def enhance_response(self, response: str) -> str:
        """Enhance response with character-specific formatting."""
        if not self.validate_response(response):
            return self._generate_fallback_response()
        
        # Basic character-consistent enhancement
        enhanced = response.strip()
        
        # Ensure response feels natural and character-appropriate
        if enhanced and not enhanced.endswith(('.', '!', '?')):
            enhanced += '.'
            
        return enhanced

    def _generate_fallback_response(self) -> str:
        """Generate character-appropriate fallback response."""
        fallbacks = [
            f"I'm not quite sure how to respond to that right now.",
            f"That's... that's an interesting question. Let me think about it.",
            f"Hmm, I need a moment to gather my thoughts on that.",
        ]
        
        # Pick fallback based on character personality
        personality_text = self._format_personality_traits().lower()
        if 'thoughtful' in personality_text:
            return fallbacks[1]
        elif 'direct' in personality_text:
            return fallbacks[0]
        else:
            return fallbacks[2]

    def get_character_info(self) -> Dict[str, Any]:
        """Get comprehensive character information."""
        base_info = self.get_agent_info()
        base_info.update({
            'character_name': self.persona.name,
            'personality_traits': self.persona.personality_traits,
            'motivations': self.persona.motivations,
            'speech_style': self.persona.speech_style,
            'relationships': self.persona.relationships,
            'current_emotional_state': self.current_emotional_state
        })
        return base_info

    def update_emotional_state(self, new_state: str) -> None:
        """Update character's current emotional state."""
        self.current_emotional_state = new_state

    def add_character_memory(self, memory: str) -> None:
        """Add a character-specific memory."""
        self.character_memories.append({
            'timestamp': datetime.now().isoformat(),
            'memory': memory
        })
        
        # Keep only recent memories (last 20)
        if len(self.character_memories) > 20:
            self.character_memories = self.character_memories[-20:]