"""
DialogueChunker - Character Index Generation for BookSouls Character Agents

Adapted from DialogueExtractor.py - Creates dialogue-focused indexes optimized for Character agents.
Focuses on preserving character voice, dialogue context, and conversation scenes.
"""

import json
import time
import datetime
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import tiktoken
from fuzzywuzzy import fuzz

try:
    from ..prompts import BASIC_DIALOGUE_EXTRACTION, CHARACTER_ANALYSIS_ENHANCED_PROMPT, format_character_data_section
    from .config.config import DialogueChunkerConfig
    from ..logs import log_llm_request, log_llm_response, LLMTimer
except ImportError:
    # For testing when running directly
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.prompts import BASIC_DIALOGUE_EXTRACTION, CHARACTER_ANALYSIS_PROMPT, CHARACTER_ANALYSIS_ENHANCED_PROMPT, format_character_data_section
    from src.chunkers.config.config import DialogueChunkerConfig
    from src.logs import log_llm_request, log_llm_response, LLMTimer

# Model integrations
try:
    import requests
    import subprocess
    OLLAMA_AVAILABLE = True
except ImportError:
    print("Warning: Requests not installed. Install with: pip install requests")
    OLLAMA_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: OpenAI not installed. Install with: pip install openai")
    OPENAI_AVAILABLE = False


def check_ollama():
    """Check if Ollama is installed and running."""
    try:
        # Check if Ollama is installed
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Ollama not installed"
        
        # Check if Ollama service is running
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            return True, "Ollama running"
        else:
            return False, "Ollama service not running"
            
    except (subprocess.CalledProcessError, requests.RequestException):
        return False, "Ollama not available"


@dataclass
class CharacterDialogue:
    """Represents a dialogue entry for character-focused agents."""
    character: str
    dialogue: str
    addressee: str  # Who the dialogue is directed to
    context: str  # Surrounding narrative context
    emotion: str  # Emotional state/tone
    actions: List[str]  # Physical actions during dialogue
    scene_id: str  # Scene/conversation identifier
    chapter_number: int
    section_id: str  # Link back to section chunk


@dataclass
class ConversationScene:
    """Represents a conversation scene with multiple characters."""
    scene_id: str
    participants: List[str]
    dialogues: List[CharacterDialogue]
    setting: str  # Where the conversation takes place
    context: str  # Overall scene context
    chapter_number: int


@dataclass
class CharacterProfile:
    """Character profile extracted from dialogue analysis."""
    name: str
    chapter_number: int
    personality_traits: List[str]
    motivations: List[str]
    speech_style: Dict[str, Any]  # formality, emotional_tendencies, etc.
    dialogue_count: int  # Number of dialogue lines in this chapter
    key_relationships: Dict[str, str]  # addressee -> relationship_type
    emotional_state: str  # Primary emotion in this chapter
    
    def to_json_string(self) -> str:
        """Return character profile as formatted JSON string for indexing."""
        profile_dict = {
            "name": self.name,
            "chapter_number": self.chapter_number,
            "personality_traits": self.personality_traits,
            "motivations": self.motivations,
            "speech_style": self.speech_style,
            "dialogue_count": self.dialogue_count,
            "key_relationships": self.key_relationships,
            "emotional_state": self.emotional_state
        }
        return json.dumps(profile_dict, indent=2)


@dataclass
class DialogueIndex:
    """Complete dialogue index for Character agents."""
    scenes: List[ConversationScene]
    by_character: Dict[str, List[CharacterDialogue]]  # Character -> their dialogues
    by_chapter: Dict[int, List[ConversationScene]]    # Chapter -> all scenes
    character_profiles: Dict[str, List[CharacterProfile]]  # Character -> chapter profiles
    total_dialogues: int
    total_scenes: int
    characters: List[str]  # All speaking characters
    chapters_covered: List[int]
    metadata: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueIndex':
        """Create DialogueIndex from dictionary (for loading from JSON)."""
        # Reconstruct scenes
        scenes = []
        for scene_data in data['scenes']:
            dialogues = []
            for d_data in scene_data['dialogues']:
                dialogue = CharacterDialogue(
                    character=d_data['character'],
                    dialogue=d_data['dialogue'],
                    addressee=d_data['addressee'],
                    context=d_data['context'],
                    emotion=d_data['emotion'],
                    actions=d_data['actions'],
                    scene_id=d_data['scene_id'],
                    chapter_number=d_data['chapter_number'],
                    section_id=d_data['section_id']
                )
                dialogues.append(dialogue)
            
            scene = ConversationScene(
                scene_id=scene_data['scene_id'],
                participants=scene_data['participants'],
                dialogues=dialogues,
                setting=scene_data['setting'],
                context=scene_data['context'],
                chapter_number=scene_data['chapter_number']
            )
            scenes.append(scene)
        
        # Reconstruct by_character
        by_character = {}
        for character, dialogues_data in data['by_character'].items():
            dialogues = []
            for d_data in dialogues_data:
                dialogue = CharacterDialogue(
                    character=d_data['character'],
                    dialogue=d_data['dialogue'],
                    addressee=d_data['addressee'],
                    context=d_data['context'],
                    emotion=d_data['emotion'],
                    actions=d_data['actions'],
                    scene_id=d_data['scene_id'],
                    chapter_number=d_data['chapter_number'],
                    section_id=d_data['section_id']
                )
                dialogues.append(dialogue)
            by_character[character] = dialogues
        
        # Reconstruct by_chapter
        by_chapter = {}
        for scene in scenes:
            chapter_num = scene.chapter_number
            if chapter_num not in by_chapter:
                by_chapter[chapter_num] = []
            by_chapter[chapter_num].append(scene)
        
        # Reconstruct character_profiles
        character_profiles = {}
        if 'character_profiles' in data:
            for character, profiles_data in data['character_profiles'].items():
                profiles = []
                for p_data in profiles_data:
                    profile = CharacterProfile(
                        name=p_data['name'],
                        chapter_number=p_data['chapter_number'],
                        personality_traits=p_data['personality_traits'],
                        motivations=p_data['motivations'],
                        speech_style=p_data['speech_style'],
                        dialogue_count=p_data['dialogue_count'],
                        key_relationships=p_data['key_relationships'],
                        emotional_state=p_data['emotional_state']
                    )
                    profiles.append(profile)
                character_profiles[character] = profiles
        
        return cls(
            scenes=scenes,
            by_character=by_character,
            by_chapter=by_chapter,
            character_profiles=character_profiles,
            total_dialogues=data['total_dialogues'],
            total_scenes=data['total_scenes'],
            characters=data['characters'],
            chapters_covered=data['chapters_covered'],
            metadata=data['metadata']
        )
    
    def get_character_profile(self, character: str, chapter: int = None) -> Optional[CharacterProfile]:
        """
        Get character profile for a specific chapter.
        
        Args:
            character: Character name
            chapter: Chapter number (if None, returns latest profile)
            
        Returns:
            CharacterProfile or None if not found
        """
        if character not in self.character_profiles:
            return None
        
        profiles = self.character_profiles[character]
        if not profiles:
            return None
        
        if chapter is None:
            # Return the latest profile
            return max(profiles, key=lambda p: p.chapter_number)
        
        # Find profile for specific chapter
        for profile in profiles:
            if profile.chapter_number == chapter:
                return profile
        
        return None
    
    def get_character_evolution(self, character: str) -> List[CharacterProfile]:
        """Get all profiles for a character showing their evolution."""
        if character not in self.character_profiles:
            return []
        
        # Return profiles sorted by chapter
        return sorted(
            self.character_profiles[character], 
            key=lambda p: p.chapter_number
        )





class DialogueChunker:
    """
    Creates DIALOGUE INDEX for BookSouls Character Agents.
    
    Optimized for:
    - Character-focused dialogue extraction
    - Preserving character voice and emotional context
    - Conversation scene organization
    - Character agent retrieval
    
    Configuration:
    The chunker is configured via DialogueChunkerConfig which controls:
    - Model settings: model_type, model_name, API credentials
    - LLM parameters: temperature, top_p, max_tokens, request_timeout
    - Extraction behavior: custom prompts, dialogue filtering
    - Logging: verbose flag for detailed processing output
    """
    
    def __init__(self, cfg: DialogueChunkerConfig = DialogueChunkerConfig()):
        """
        Initialize the dialogue chunker with configuration.
        
        Args:
            cfg: DialogueChunkerConfig instance with all settings
        """
        self.cfg = cfg
        
        # Initialize tokenizer for token counting
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Set model name from config or use default
        self.model_name = self.cfg.model_name or self.cfg.get_default_model_name()
        
        # Setup model-specific configurations
        if self.cfg.model_type == "ollama":
            if not OLLAMA_AVAILABLE:
                raise RuntimeError("Ollama dependencies not available. Install with: pip install requests")
            self.ollama_url = self.cfg.ollama_url
            
        elif self.cfg.model_type == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI dependencies not available. Install with: pip install openai")
            
            # Setup OpenAI client
            api_key = self.cfg.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass in config")
            
            self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Set extraction prompt (use custom prompt or default)
        self.extraction_prompt = self.cfg.custom_prompt if self.cfg.custom_prompt is not None else BASIC_DIALOGUE_EXTRACTION
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
    
    def create_dialogue_index(self, chapters: List) -> DialogueIndex:
        """
        Create dialogue index from chapters for Character agents.
        
        Args:
            chapters: List of ChapterChunk objects from PDF extractor
            
        Returns:
            DialogueIndex optimized for Character agents
        """
        if self.cfg.verbose:
            print(f"Creating dialogue index from {len(chapters)} chapters...")
        start_time = time.time()
        
        all_scenes = []
        scene_counter = 0
        total_dialogues = 0
        
        for chapter in chapters:
            if self.cfg.verbose:
                print(f"Processing Chapter {chapter.chapter_number}: {chapter.chapter_title}")
            
            # Use existing chunks from PDF extractor
            existing_chunks = chapter.chunks
            
            for i, chunk_text in enumerate(existing_chunks):
                # Skip chunks with minimal dialogue potential if configured
                if self.cfg.skip_non_dialogue and not self._has_dialogue_markers(chunk_text):
                    continue
                
                try:
                    scene = self._extract_scene_dialogues(
                        chunk_text, 
                        chapter.chapter_number,
                        f"ch{chapter.chapter_number}_scene{scene_counter}",
                        f"ch{chapter.chapter_number}_sec{i}"  # section_id
                    )
                    
                    if scene and scene.dialogues:
                        all_scenes.append(scene)
                        total_dialogues += len(scene.dialogues)
                        scene_counter += 1
                        
                except Exception as e:
                    if self.cfg.verbose:
                        print(f"Warning: Failed to process chunk {i} in Chapter {chapter.chapter_number}: {str(e)}")
                    continue
        
        # Organize by character and chapter
        by_character = self._organize_by_character(all_scenes)
        # Normalize character names using fuzzy matching
        by_character = self._normalize_character_index(by_character)
        by_chapter = self._organize_by_chapter(all_scenes)
        characters = list(by_character.keys())
        chapters_covered = [ch.chapter_number for ch in chapters]
        
        # Analyze characters chapter by chapter
        character_profiles = {}
        if self.cfg.verbose:
            print("Starting character analysis...")
        
        for chapter_num, chapter_scenes in by_chapter.items():
            if self.cfg.verbose:
                print(f"Analyzing characters in Chapter {chapter_num}...")
            
            # Select top characters for this chapter
            selected_characters = self._select_characters_for_analysis(chapter_scenes)
            
            if selected_characters:
                try:
                    # Analyze selected characters
                    profiles = self._analyze_chapter_characters(
                        selected_characters, chapter_scenes, chapter_num
                    )
                    
                    # Store profiles by character
                    for profile in profiles:
                        if profile.name not in character_profiles:
                            character_profiles[profile.name] = []
                        character_profiles[profile.name].append(profile)
                        
                except Exception as e:
                    if self.cfg.verbose:
                        print(f"Warning: Failed to analyze characters in Chapter {chapter_num}: {str(e)}")
                    continue
        
        processing_time = time.time() - start_time
        
        # Create dialogue index with character profiles
        dialogue_index = DialogueIndex(
            scenes=all_scenes,
            by_character=by_character,
            by_chapter=by_chapter,
            character_profiles=character_profiles,
            total_dialogues=total_dialogues,
            total_scenes=len(all_scenes),
            characters=characters,
            chapters_covered=chapters_covered,
            metadata={
                'processing_time': processing_time,
                'model_type': self.cfg.model_type,
                'model_name': self.model_name,
                'created_at': datetime.datetime.now().isoformat(),
                'avg_dialogues_per_scene': total_dialogues / len(all_scenes) if all_scenes else 0,
                'characters_analyzed': len(character_profiles),
                'total_character_profiles': sum(len(profiles) for profiles in character_profiles.values()),
                'config_used': {
                    'model_type': self.cfg.model_type,
                    'model_name': self.model_name,
                    'temperature': self.cfg.temperature,
                    'max_tokens': self.cfg.max_tokens,
                    'skip_non_dialogue': self.cfg.skip_non_dialogue,
                    'top_characters_per_chapter': self.cfg.top_characters_per_chapter,
                    'max_sample_dialogues': self.cfg.max_sample_dialogues
                }
            }
        )
        
        if self.cfg.verbose:
            print(f"Created dialogue index:")
            print(f"   Scenes: {len(all_scenes)}")
            print(f"   Dialogues: {total_dialogues}")
            print(f"   Characters: {len(characters)}")
            print(f"   Characters analyzed: {len(character_profiles)}")
            print(f"   Total character profiles: {sum(len(profiles) for profiles in character_profiles.values())}")
            print(f"   Processing time: {processing_time:.2f}s")
        
        return dialogue_index
    
    def _has_dialogue_markers(self, text: str) -> bool:
        """Quick check if text likely contains dialogue."""
        markers = ['"', "'", """, """, "'", "'"]
        return any(marker in text for marker in markers)
    
    def _extract_scene_dialogues(self, chunk_text: str, chapter_num: int, 
                               scene_id: str, section_id: str) -> Optional[ConversationScene]:
        """Extract dialogues from a single text chunk using specified LLM."""
        
        # Prepare prompt
        prompt = self.extraction_prompt.format(text_chunk=chunk_text)
        
        # Generate response based on model type
        if self.cfg.model_type == "ollama":
            response_text = self._generate_ollama_response(prompt)
        else:
            response_text = self._generate_openai_response(prompt)
            
        if not response_text:
            return None
        
        # Extract JSON from response
        print(f"DEBUG: OpenAI response: {(response_text)}")
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                return None
                
            json_str = response_text[json_start:json_end]
            dialogue_data = json.loads(json_str)
            
            return self._build_conversation_scene(
                dialogue_data, 
                chapter_num, 
                scene_id, 
                section_id,
                chunk_text
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {str(e)}")
            return None
    
    def _generate_ollama_response(self, prompt: str) -> Optional[str]:
        """Generate response using configured Ollama API."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.cfg.temperature,
                "top_p": self.cfg.top_p,
                "num_predict": self.cfg.max_tokens,
                "stop": self.cfg.ollama_stop_tokens
            }
        }
        
        # Log the request
        log_id = log_llm_request(
            model_type="ollama",
            model_name=self.model_name,
            request_type="dialogue_extraction",
            prompt=prompt,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            metadata={"top_p": self.cfg.top_p}
        )
        
        try:
            with LLMTimer("ollama_request") as timer:
                response = requests.post(self.ollama_url, json=payload, timeout=self.cfg.request_timeout)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('response', '')
            
            # Log the successful response
            log_llm_response(
                log_id,
                response_text,
                response_time_ms=int(timer.get_elapsed_ms()),
                token_count_input=self._count_tokens(prompt),
                token_count_output=self._count_tokens(response_text) if response_text else 0
            )
            
            return response_text
            
        except requests.RequestException as e:
            error_msg = f"Ollama API error: {str(e)}"
            log_llm_response(log_id, "", error=error_msg)
            
            if self.cfg.verbose:
                print(error_msg)
            return None
    
    def _generate_openai_response(self, prompt: str) -> Optional[str]:
        """Generate response using configured OpenAI API."""
        # Log the request
        log_id = log_llm_request(
            model_type="openai",
            model_name=self.model_name,
            request_type="dialogue_extraction",
            prompt=prompt,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            metadata={"top_p": self.cfg.top_p}
        )
        
        try:
            # Use config to build request parameters
            request_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "You are an expert at extracting dialogue from fantasy novels. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.cfg.temperature,
                "top_p": self.cfg.top_p,
                "max_tokens": self.cfg.max_tokens,
                "timeout": self.cfg.request_timeout
            }
            
            # Add JSON mode if configured
            if self.cfg.use_json_mode:
                request_params["response_format"] = {"type": "json_object"}
            
            with LLMTimer("openai_request") as timer:
                response = self.openai_client.chat.completions.create(**request_params)
                response_text = response.choices[0].message.content
            
            # Log the successful response
            log_llm_response(
                log_id,
                response_text,
                response_time_ms=int(timer.get_elapsed_ms()),
                token_count_input=response.usage.prompt_tokens if hasattr(response, 'usage') else self._count_tokens(prompt),
                token_count_output=response.usage.completion_tokens if hasattr(response, 'usage') else self._count_tokens(response_text)
            )
            
            return response_text
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            log_llm_response(log_id, "", error=error_msg)
            
            if self.cfg.verbose:
                print(error_msg)
            return None
    
    def _generate_ollama_character_analysis_response(self, prompt: str) -> Optional[str]:
        """Generate character analysis response using configured Ollama API."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.cfg.temperature,
                "top_p": self.cfg.top_p,
                "num_predict": self.cfg.max_tokens,
                "stop": self.cfg.ollama_stop_tokens
            }
        }
        
        # Log the request
        log_id = log_llm_request(
            model_type="ollama",
            model_name=self.model_name,
            request_type="character_analysis",
            prompt=prompt,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            metadata={"top_p": self.cfg.top_p}
        )
        
        try:
            with LLMTimer("ollama_character_analysis") as timer:
                response = requests.post(self.ollama_url, json=payload, timeout=self.cfg.request_timeout)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('response', '')
            
            # Log the successful response
            log_llm_response(
                log_id,
                response_text,
                response_time_ms=int(timer.get_elapsed_ms()),
                token_count_input=self._count_tokens(prompt),
                token_count_output=self._count_tokens(response_text) if response_text else 0
            )
            
            return response_text
            
        except requests.RequestException as e:
            error_msg = f"Ollama API error: {str(e)}"
            log_llm_response(log_id, "", error=error_msg)
            
            if self.cfg.verbose:
                print(error_msg)
            return None
    
    def _generate_openai_character_analysis_response(self, prompt: str) -> Optional[str]:
        """Generate character analysis response using configured OpenAI API."""
        # Log the request
        log_id = log_llm_request(
            model_type="openai",
            model_name=self.model_name,
            request_type="character_analysis",
            prompt=prompt,
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            metadata={"top_p": self.cfg.top_p}
        )
        
        try:
            # Use config to build request parameters
            request_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "You are an expert literary analyst specializing in character psychology and development. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.cfg.temperature,
                "top_p": self.cfg.top_p,
                "max_tokens": self.cfg.max_tokens,
                "timeout": self.cfg.request_timeout
            }
            
            # Add JSON mode if configured
            if self.cfg.use_json_mode:
                request_params["response_format"] = {"type": "json_object"}
            
            with LLMTimer("openai_character_analysis") as timer:
                response = self.openai_client.chat.completions.create(**request_params)
                response_text = response.choices[0].message.content
            
            # Log the successful response
            log_llm_response(
                log_id,
                response_text,
                response_time_ms=int(timer.get_elapsed_ms()),
                token_count_input=response.usage.prompt_tokens if hasattr(response, 'usage') else self._count_tokens(prompt),
                token_count_output=response.usage.completion_tokens if hasattr(response, 'usage') else self._count_tokens(response_text)
            )
            
            return response_text
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            log_llm_response(log_id, "", error=error_msg)
            
            if self.cfg.verbose:
                print(error_msg)
            return None
    
    def _build_conversation_scene(self, dialogue_data: Dict, chapter_num: int, 
                                scene_id: str, section_id: str, original_text: str) -> ConversationScene:
        """Build a ConversationScene from extracted dialogue data."""
        
        dialogues = []
        
        for dialogue_entry in dialogue_data.get("dialogues", []):
            char_dialogue = CharacterDialogue(
                character=dialogue_entry.get("speaker", "Unknown"),
                dialogue=dialogue_entry.get("dialogue", ""),
                addressee=dialogue_entry.get("addressee", "Unknown"),
                context=dialogue_entry.get("context", ""),
                emotion=dialogue_entry.get("emotion", "neutral"),
                actions=dialogue_entry.get("actions", []),
                scene_id=scene_id,
                chapter_number=chapter_num,
                section_id=section_id
            )
            dialogues.append(char_dialogue)
        
        return ConversationScene(
            scene_id=scene_id,
            participants=dialogue_data.get("participants", []),
            dialogues=dialogues,
            setting=dialogue_data.get("scene_setting", ""),
            context=original_text[:200] + "...",  # Brief context
            chapter_number=chapter_num
        )
    
    def _organize_by_character(self, scenes: List[ConversationScene]) -> Dict[str, List[CharacterDialogue]]:
        """Build CHARACTER INDEX: Group all dialogues by character for character agents."""
        character_index = {}
        
        for scene in scenes:
            for dialogue in scene.dialogues:
                character = dialogue.character
                
                if character not in character_index:
                    character_index[character] = []
                
                character_index[character].append(dialogue)
        
        # Sort each character's dialogues by chapter
        for character in character_index:
            character_index[character].sort(
                key=lambda d: d.chapter_number
            )
        
        return character_index
    
    def _normalize_character_index(self, by_character: Dict[str, List[CharacterDialogue]]) -> Dict[str, List[CharacterDialogue]]:
        """Simple character name normalization using fuzzy matching. E.g. "Tom" -> "Tomas" -> "Tomas" or Bilbo Baggins -> Bilbo"""
        normalized_index = {}
        
        for character, dialogues in by_character.items():
            # Find best canonical match
            canonical = character
            for existing_char in normalized_index.keys():
                if fuzz.token_sort_ratio(character.lower(), existing_char.lower()) >= 85:
                    canonical = existing_char
                    break
            
            # Merge dialogues under canonical name
            if canonical not in normalized_index:
                normalized_index[canonical] = []
            normalized_index[canonical].extend(dialogues)
        
        if self.cfg.verbose and len(normalized_index) < len(by_character):
            print(f"Character normalization: {len(by_character)} -> {len(normalized_index)} unique characters")
        
        return normalized_index
    
    def _organize_by_chapter(self, scenes: List[ConversationScene]) -> Dict[int, List[ConversationScene]]:
        """Organize scenes by chapter."""
        by_chapter = {}
        
        for scene in scenes:
            chapter_num = scene.chapter_number
            if chapter_num not in by_chapter:
                by_chapter[chapter_num] = []
            by_chapter[chapter_num].append(scene)
        
        return by_chapter
    
    def _select_characters_for_analysis(self, chapter_scenes: List[ConversationScene]) -> List[str]:
        """
        Select top N characters by dialogue count for chapter analysis.
        
        Args:
            chapter_scenes: All scenes in the chapter
            
        Returns:
            List of character names selected for analysis
        """
        # Count dialogues per character in this chapter
        character_dialogue_count = {}
        
        for scene in chapter_scenes:
            for dialogue in scene.dialogues:
                character = dialogue.character
                character_dialogue_count[character] = character_dialogue_count.get(character, 0) + 1
        
        # Sort by dialogue count and take top N
        sorted_characters = sorted(
            character_dialogue_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Return top N character names based on config
        top_n = self.cfg.top_characters_per_chapter
        selected = [char for char, _count in sorted_characters[:top_n]]
        
        if self.cfg.verbose and selected:
            counts_str = ", ".join([f"{char}({character_dialogue_count[char]})" for char in selected])
            print(f"Selected characters for analysis: {counts_str}")
        
        return selected
    
    def _analyze_chapter_characters(self, selected_characters: List[str], 
                                  chapter_scenes: List[ConversationScene],
                                  chapter_num: int) -> List[CharacterProfile]:
        """
        Analyze selected characters using LLM for a specific chapter.
        
        Args:
            selected_characters: List of character names to analyze
            chapter_scenes: All scenes in the chapter
            chapter_num: Chapter number being analyzed
            
        Returns:
            List of CharacterProfile objects for the analyzed characters
        """
        if not selected_characters:
            return []
        
        profiles = []
        
        for character in selected_characters:
            if self.cfg.verbose:
                print(f"  Analyzing character: {character}")
                
            try:
                # Analyze each character individually
                character_profile = self._analyze_single_character(
                    character, chapter_scenes, chapter_num
                )
                
                if character_profile:
                    profiles.append(character_profile)
                    
            except Exception as e:
                if self.cfg.verbose:
                    print(f"Warning: Failed to analyze character {character} in Chapter {chapter_num}: {str(e)}")
                continue
        
        if self.cfg.verbose:
            print(f"  Successfully analyzed {len(profiles)}/{len(selected_characters)} characters")
        
        return profiles
    
    def _analyze_single_character(self, character: str, 
                                chapter_scenes: List[ConversationScene],
                                chapter_num: int) -> Optional[CharacterProfile]:
        """
        Analyze a single character using individual LLM request for focused analysis.
        
        Args:
            character: Character name to analyze
            chapter_scenes: All scenes in the chapter
            chapter_num: Chapter number being analyzed
            
        Returns:
            CharacterProfile object or None if analysis failed
        """
        # Use emotion-based sampling for this single character
        character_data = self._prepare_character_data_for_analysis([character], chapter_scenes)
        
        if character not in character_data or not character_data[character]['dialogue_entries']:
            if self.cfg.verbose:
                print(f"    No dialogue data found for {character}")
            return None
        
        # Create focused prompt for just this character
        prompt = self._create_single_character_analysis_prompt(
            character_data[character], character, chapter_num
        )
        
        # Generate response based on model type
        if self.cfg.model_type == "ollama":
            response_text = self._generate_ollama_character_analysis_response(prompt)
        else:
            response_text = self._generate_openai_character_analysis_response(prompt)
        
        if not response_text:
            if self.cfg.verbose:
                print(f"    No response from LLM for {character}")
            return None
        
        # Parse single character response
        return self._parse_single_character_response(
            response_text, character, chapter_scenes, chapter_num
        )
    
    def _create_single_character_analysis_prompt(
        self,
        character_data: Dict[str, Any],
        character_name: str,
        chapter_num: int,
    ) -> str:
        """
        Build the enhanced analysis prompt for ONE character using the
        new single-character template.
        """
        # Build the character-specific data section (new signature = name first)
        character_data_section = format_character_data_section(
            character_name,
            character_data,
            max_dialogues=len(character_data.get("dialogue_entries", [])),
        )

        # Fill the template’s placeholders (character_name, chapter_num, character_data_section)
        prompt = CHARACTER_ANALYSIS_ENHANCED_PROMPT.format(
            character_name=character_name,
            chapter_num=chapter_num,
            character_data_section=character_data_section,
        )

        return prompt
        
    def _prepare_character_data_for_analysis(self, characters: List[str], 
                                           chapter_scenes: List[ConversationScene]) -> Dict[str, Any]:
        """
        Prepare character dialogue data for LLM analysis with emotion-based sampling.
        
        Strategy:
        1. Group dialogues by emotion for each character
        2. Select the longest dialogue from each emotion group
        3. Sort selected dialogues by length (longest first)
        4. Apply max_sample_dialogues limit (if > 0)
        
        Example behavior:
        Before (chronological): Character A gets 7 dialogues, possibly all "neutral" from early scenes
        After (emotion-based): Character A gets dialogues like:
        - "angry" (85 chars), "sad" (72 chars), "joyful" (68 chars), "fearful" (45 chars), 
          "neutral" (38 chars), "confused" (22 chars), "determined" (15 chars)
        - If max_sample_dialogues = 4: takes angry, sad, joyful, fearful
        - If max_sample_dialogues = 0: takes all 7 emotions (no limit)
        """
        character_data = {}
        
        for character in characters:
            # Step 1: Group dialogues by emotion
            emotion_groups = {}  # emotion -> list of dialogues
            addressees = set()
            emotions = []
            
            # Collect all dialogues for this character, grouped by emotion
            for scene in chapter_scenes:
                for dialogue in scene.dialogues:
                    if dialogue.character == character:
                        emotion = dialogue.emotion
                        if emotion not in emotion_groups:
                            emotion_groups[emotion] = []
                        emotion_groups[emotion].append(dialogue)
                        addressees.add(dialogue.addressee)
                        emotions.append(dialogue.emotion)
            
            # Step 2: Select one dialogue per emotion (longest one)
            selected_dialogues = []
            for emotion, dialogues in emotion_groups.items():
                # Pick the longest dialogue from this emotion group
                longest = max(dialogues, key=lambda d: len(d.dialogue))
                selected_dialogues.append(longest)
            
            # Step 3: Sort by dialogue length (descending - longest first)
            selected_dialogues.sort(key=lambda d: len(d.dialogue), reverse=True)
            
            # Step 4: Apply max_sample_dialogues limit
            if self.cfg.max_sample_dialogues > 0:
                selected_dialogues = selected_dialogues[:self.cfg.max_sample_dialogues]
            # If max_sample_dialogues = 0, take all emotion-sampled dialogues (no limit)
            
            # Convert to the expected format
            dialogue_entries = []
            for dialogue in selected_dialogues:
                dialogue_entries.append({
                    'dialogue': dialogue.dialogue,
                    'addressee': dialogue.addressee,
                    'actions': dialogue.actions,
                    'emotion': dialogue.emotion
                })
            
            if self.cfg.verbose and dialogue_entries:
                emotions_selected = [entry['emotion'] for entry in dialogue_entries]
                print(f"  {character}: Selected {len(dialogue_entries)} dialogues covering emotions: {emotions_selected}")
            
            character_data[character] = {
                'dialogue_entries': dialogue_entries,
                'addressees': list(addressees),
                'emotions': emotions
            }
        
        return character_data
    
    def _create_character_analysis_prompt(self, character_data: Dict[str, Any], 
                                        chapter_num: int) -> str:
        """Create the character analysis prompt for LLM using template."""
        
        # Format character data section using configurable limits
        character_data_section = format_character_data_section(
            character_data, 
            max_dialogues=self.cfg.max_sample_dialogues
        )
        
        # Use the template prompt
        return CHARACTER_ANALYSIS_PROMPT.format(
            character_count=len(character_data),
            chapter_num=chapter_num,
            character_data_section=character_data_section
        )
    
    def _parse_character_analysis_response(self, response_text: str, 
                                         selected_characters: List[str],
                                         chapter_scenes: List[ConversationScene],
                                         chapter_num: int) -> List[CharacterProfile]:
        """Parse LLM response and create CharacterProfile objects."""
        profiles = []
        
        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                if self.cfg.verbose:
                    print(f"Warning: No JSON found in character analysis response for Chapter {chapter_num}")
                return []
                
            json_str = response_text[json_start:json_end]
            analysis_data = json.loads(json_str)
            
            # Count dialogues for each character in this chapter
            character_dialogue_counts = {}
            for scene in chapter_scenes:
                for dialogue in scene.dialogues:
                    char = dialogue.character
                    character_dialogue_counts[char] = character_dialogue_counts.get(char, 0) + 1
            
            # Create CharacterProfile for each analyzed character
            for character in selected_characters:
                if character in analysis_data:
                    char_data = analysis_data[character]
                    
                    profile = CharacterProfile(
                        name=character,
                        chapter_number=chapter_num,
                        personality_traits=char_data.get("personality_traits", []),
                        motivations=char_data.get("motivations", []),
                        speech_style=char_data.get("speech_style", {}),
                        dialogue_count=character_dialogue_counts.get(character, 0),
                        key_relationships=char_data.get("key_relationships", {}),
                        emotional_state=char_data.get("emotional_state", "neutral")
                    )
                    profiles.append(profile)
                    
                    if self.cfg.verbose:
                        print(f"Created profile for {character}: {profile.personality_traits}")
            
            return profiles
            
        except (json.JSONDecodeError, KeyError) as e:
            if self.cfg.verbose:
                print(f"Warning: Failed to parse character analysis response for Chapter {chapter_num}: {str(e)}")
            return []

    def _parse_single_character_response(
        self,
        response_text: str,
        character: str,
        chapter_scenes: List[ConversationScene],
        chapter_num: int,
    ) -> Optional[CharacterProfile]:
        """
        Parse LLM JSON response produced by the single‑character prompt and
        convert it into a CharacterProfile.

        Args:
            response_text: Raw LLM output.
            character: Character name we asked to analyse.
            chapter_scenes: All scenes in the current chapter.
            chapter_num: Current chapter number.

        Returns:
            CharacterProfile object if parsing succeeds, else None.
        """
        # Locate the JSON substring
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            if self.cfg.verbose:
                print(
                    f"Warning: No JSON found in single‑character analysis for {character} (Chapter {chapter_num})"
                )
            return None

        try:
            payload = json.loads(response_text[json_start:json_end])
        except json.JSONDecodeError as exc:
            if self.cfg.verbose:
                print(
                    f"Warning: JSON parse error for {character} (Chapter {chapter_num}): {exc}"
                )
            return None

        # If wrapped by character_name key → unwrap
        if character in payload:
            payload = payload[character]

        # Basic validation
        if not isinstance(payload, dict) or "personality_traits" not in payload:
            if self.cfg.verbose:
                print(
                    f"Warning: Unexpected schema for {character} (Chapter {chapter_num})"
                )
            return None

        # Count dialogues for this character in the chapter
        dialogue_count = 0
        for scene in chapter_scenes:
            for dlg in scene.dialogues:
                if dlg.character == character:
                    dialogue_count += 1

        return CharacterProfile(
            name=character,
            chapter_number=chapter_num,
            personality_traits=payload.get("personality_traits", []),
            motivations=payload.get("motivations", []),
            speech_style=payload.get("voice", {}),
            dialogue_count=dialogue_count,
            key_relationships=payload.get("relationships", {}),
            emotional_state=payload.get("emotional_profile", {}).get(
                "current_state", "neutral"
            ),
        )
    
    def get_dialogue_chunks(self, dialogue_index: DialogueIndex) -> List[str]:
        """
        Get dialogue chunks ready for vector database indexing.
        
        Returns:
            List of enhanced dialogue chunks optimized for Character agent retrieval
        """
        chunks = []
        
        for scene in dialogue_index.scenes:
            # Create scene-based chunk
            scene_text = f"Scene: {scene.setting}\n" if scene.setting else ""
            scene_text += f"Participants: {', '.join(scene.participants)}\n\n" if scene.participants else ""
            
            for dialogue in scene.dialogues:
                scene_text += f"{dialogue.character}: \"{dialogue.dialogue}\"\n"
                if dialogue.actions:
                    scene_text += f"Actions: {', '.join(dialogue.actions)}\n"
                scene_text += f"Emotion: {dialogue.emotion}\n\n"
            
            chunks.append(scene_text)
        
        return chunks
    
    def get_character_chunks(self, dialogue_index: DialogueIndex) -> Dict[str, List[str]]:
        """
        Get character-specific chunks for individual character agents.
        
        Returns:
            Dictionary mapping character names to their dialogue chunks
        """
        character_chunks = {}
        
        for character, dialogues in dialogue_index.by_character.items():
            character_chunks[character] = []
            
            for dialogue in dialogues:
                chunk_text = f"Character: {dialogue.character}\n"
                chunk_text += f"Chapter {dialogue.chapter_number}\n"
                chunk_text += f"To: {dialogue.addressee}\n"
                chunk_text += f"Emotion: {dialogue.emotion}\n\n"
                chunk_text += f'"{dialogue.dialogue}"\n\n'
                if dialogue.context:
                    chunk_text += f"Context: {dialogue.context}"
                
                character_chunks[character].append(chunk_text)
        
        return character_chunks
    
    def save_dialogue_index(self, dialogue_index: DialogueIndex, filepath: str = None):
        """Save dialogue index to JSON file with unique timestamp."""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"./dialogue_index_{timestamp}.json"
        else:
            # Add timestamp to provided filepath
            base_name = os.path.splitext(filepath)[0]
            extension = os.path.splitext(filepath)[1] or '.json'
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{base_name}_{timestamp}{extension}"
        
        # Convert to serializable format
        serializable_data = {
            'scenes': [
                {
                    'scene_id': scene.scene_id,
                    'participants': scene.participants,
                    'setting': scene.setting,
                    'context': scene.context,
                    'chapter_number': scene.chapter_number,
                    'dialogues': [
                        {
                            'character': d.character,
                            'dialogue': d.dialogue,
                            'addressee': d.addressee,
                            'context': d.context,
                            'emotion': d.emotion,
                            'actions': d.actions,
                            'scene_id': d.scene_id,
                            'chapter_number': d.chapter_number,
                            'section_id': d.section_id
                        }
                        for d in scene.dialogues
                    ]
                }
                for scene in dialogue_index.scenes
            ],
            'by_character': {
                character: [
                    {
                        'character': d.character,
                        'dialogue': d.dialogue,
                        'addressee': d.addressee,
                        'context': d.context,
                        'emotion': d.emotion,
                        'actions': d.actions,
                        'scene_id': d.scene_id,
                        'chapter_number': d.chapter_number,
                        'section_id': d.section_id
                    }
                    for d in dialogues
                ]
                for character, dialogues in dialogue_index.by_character.items()
            },
            'character_profiles': {
                character: [
                    {
                        'name': p.name,
                        'chapter_number': p.chapter_number,
                        'personality_traits': p.personality_traits,
                        'motivations': p.motivations,
                        'speech_style': p.speech_style,
                        'dialogue_count': p.dialogue_count,
                        'key_relationships': p.key_relationships,
                        'emotional_state': p.emotional_state
                    }
                    for p in profiles
                ]
                for character, profiles in dialogue_index.character_profiles.items()
            },
            'total_dialogues': dialogue_index.total_dialogues,
            'total_scenes': dialogue_index.total_scenes,
            'characters': dialogue_index.characters,
            'chapters_covered': dialogue_index.chapters_covered,
            'metadata': dialogue_index.metadata
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        if self.cfg.verbose:
            print(f"Dialogue index saved to {filepath}")
            print(f"Configuration used: {self.cfg.model_type} model '{self.model_name}' with {self.cfg.max_tokens} max tokens")
        return filepath

    @staticmethod
    def load_dialogue_index(filepath: str) -> DialogueIndex:
        """Load dialogue index from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct DialogueIndex from saved data
        return DialogueIndex.from_dict(data)


# Factory functions
def create_dialogue_chunker(config: DialogueChunkerConfig = None) -> DialogueChunker:
    """
    Factory function to create a dialogue chunker.
    
    Args:
        config: Optional DialogueChunkerConfig. If None, uses default configuration.
        
    Returns:
        Configured DialogueChunker instance ready for processing
    """
    if config is None:
        config = DialogueChunkerConfig()
    return DialogueChunker(config)

def create_ollama_dialogue_chunker(model_name: str = "llama3.1:8b-instruct-q4_0", 
                                  custom_prompt: str = None, **kwargs) -> DialogueChunker:
    """Create an Ollama-based dialogue chunker with specified model."""
    config = DialogueChunkerConfig(
        model_type="ollama", 
        model_name=model_name, 
        custom_prompt=custom_prompt,
        **kwargs
    )
    return DialogueChunker(config)

def create_openai_dialogue_chunker(api_key: str = None, 
                                  model_name: str = "gpt-4o-mini", 
                                  custom_prompt: str = None, **kwargs) -> DialogueChunker:
    """Create an OpenAI-based dialogue chunker with specified model."""
    config = DialogueChunkerConfig(
        model_type="openai", 
        model_name=model_name, 
        api_key=api_key, 
        custom_prompt=custom_prompt,
        **kwargs
    )
    return DialogueChunker(config)