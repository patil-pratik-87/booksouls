"""
DialogueChunker - Character Index Generation for BookSouls Character Agents

Adapted from DialogueExtractor.py - Creates dialogue-focused indexes optimized for Character agents.
Focuses on preserving character voice, dialogue context, and conversation scenes.
"""

import json
import time
import datetime
import os
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass
from enum import Enum
import tiktoken
from fuzzywuzzy import fuzz

try:
    from ..prompts import BASIC_DIALOGUE_EXTRACTION
    from .config.config import DialogueChunkerConfig
except ImportError:
    # For testing when running directly
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.prompts import BASIC_DIALOGUE_EXTRACTION
    from src.chunkers.config.config import DialogueChunkerConfig

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
class DialogueIndex:
    """Complete dialogue index for Character agents."""
    scenes: List[ConversationScene]
    by_character: Dict[str, List[CharacterDialogue]]  # Character -> their dialogues
    by_chapter: Dict[int, List[ConversationScene]]    # Chapter -> all scenes
    total_dialogues: int
    total_scenes: int
    characters: List[str]  # All speaking characters
    chapters_covered: List[int]
    metadata: Dict[str, Any]





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
        
        processing_time = time.time() - start_time
        
        # Create dialogue index
        dialogue_index = DialogueIndex(
            scenes=all_scenes,
            by_character=by_character,
            by_chapter=by_chapter,
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
                'config_used': {
                    'model_type': self.cfg.model_type,
                    'model_name': self.model_name,
                    'temperature': self.cfg.temperature,
                    'max_tokens': self.cfg.max_tokens,
                    'skip_non_dialogue': self.cfg.skip_non_dialogue
                }
            }
        )
        
        if self.cfg.verbose:
            print(f"Created dialogue index:")
            print(f"   Scenes: {len(all_scenes)}")
            print(f"   Dialogues: {total_dialogues}")
            print(f"   Characters: {len(characters)}")
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
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=self.cfg.request_timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.RequestException as e:
            if self.cfg.verbose:
                print(f"Ollama API error: {str(e)}")
            return None
    
    def _generate_openai_response(self, prompt: str) -> Optional[str]:
        """Generate response using configured OpenAI API."""
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
            
            response = self.openai_client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content
            
        except Exception as e:
            if self.cfg.verbose:
                print(f"OpenAI API error: {str(e)}")
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
        """Simple character name normalization using fuzzy matching."""
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