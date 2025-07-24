import json
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
import os
from enum import Enum

# Model integrations
try:
    import requests
    import subprocess
    OLLAMA_AVAILABLE = True
except ImportError:
    print("Requests not installed. Install with: pip install requests")
    OLLAMA_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print(" OpenAI not installed. Install with: pip install openai")
    OPENAI_AVAILABLE = False

# Import prompts
from src.prompts import BASIC_DIALOGUE_EXTRACTION, ADVANCED_DIALOGUE_EXTRACTION

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

@dataclass
class ConversationScene:
    """Represents a conversation scene with multiple characters."""
    scene_id: str
    participants: List[str]
    dialogues: List[CharacterDialogue]
    setting: str  # Where the conversation takes place
    context: str  # Overall scene context
    chapter_number: int


class ModelType(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class DialogueExtractor:
    """
    LLM-based dialogue extractor using Llama 3.1 8B for fast and efficient
    character-focused dialogue extraction for BookSouls CHARACTER INDEX.
    """
    
    def __init__(self, 
                 model_type: Literal["ollama", "openai"] = "ollama",
                 model_name: str = None,
                 api_key: str = None,
                 prompt: str = None):
        """
        Initialize the dialogue extractor with specified model type and custom prompt.
        
        Args:
            model_type: "ollama" for local Llama or "openai" for GPT-4o-mini
            model_name: Model identifier (defaults: llama3.1:8b-instruct-q4_0 or gpt-4o-mini)
            api_key: OpenAI API key (if using OpenAI, defaults to OPENAI_API_KEY env var)
            prompt: Custom prompt template (defaults to BASIC_DIALOGUE_EXTRACTION if not provided)
        """
        self.model_type = ModelType(model_type)
        
        # Set default model names
        if model_name is None:
            if self.model_type == ModelType.OLLAMA:
                self.model_name = "llama3.1:8b-instruct-q4_0"
            else:
                self.model_name = "gpt-4o-mini"
        else:
            self.model_name = model_name
            
        # Setup model-specific configurations
        if self.model_type == ModelType.OLLAMA:
            if not OLLAMA_AVAILABLE:
                raise RuntimeError("Ollama dependencies not available. Install with: pip install requests")
            self.ollama_url = "http://localhost:11434/api/generate"
            
        elif self.model_type == ModelType.OPENAI:
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI dependencies not available. Install with: pip install openai")
            
            # Setup OpenAI client
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter")
            
            self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Set extraction prompt (use custom prompt or default to basic)
        self.extraction_prompt = prompt if prompt is not None else BASIC_DIALOGUE_EXTRACTION
    
    
    def extract_dialogues_from_chapters(self, chunker, chapters: List) -> List[ConversationScene]:
        """
        Extract character-focused dialogues from chapters using token chunks.
        
        Args:
            chapters: List of ChapterChunk objects from ChunkAccuracyTester
            
        Returns:
            List of ConversationScene objects for CHARACTER INDEX
        """
        print(f"Extracting dialogues from {len(chapters)} chapters...")
        all_scenes = []
        scene_counter = 0
        
        for chapter in chapters:
            print(f"Processing Chapter {chapter.chapter_number}: {chapter.chapter_title}")
            
            token_chunks = chunker.get_token_chunks_for_processing([chapter])
            
            for i, chunk_text in enumerate(token_chunks):
                # Skip chunks with minimal dialogue potential
                if not self._has_dialogue_markers(chunk_text):
                    continue
                
                try:
                    scene = self._extract_scene_dialogues(
                        chunk_text, 
                        chapter.chapter_number,
                        f"ch{chapter.chapter_number}_scene{scene_counter}"
                    )
                    
                    if scene and scene.dialogues:
                        all_scenes.append(scene)
                        scene_counter += 1
                        
                except Exception as e:
                    print(f"Warning: Failed to process chunk {i} in Chapter {chapter.chapter_number}: {str(e)}")
                    continue
        
        print(f"Extracted {len(all_scenes)} conversation scenes")
        return all_scenes
    
    def _has_dialogue_markers(self, text: str) -> bool:
        """Quick check if text likely contains dialogue."""
        markers = ['"', "'", """, """, "'", "'"]
        return any(marker in text for marker in markers)
    
    def _extract_scene_dialogues(self, chunk_text: str, chapter_num: int, scene_id: str) -> Optional[ConversationScene]:
        """Extract dialogues from a single text chunk using specified LLM."""
        
        # Prepare prompt
        prompt = self.extraction_prompt.format(text_chunk=chunk_text)
        
        # Generate response based on model type
        if self.model_type == ModelType.OLLAMA:
            response_text = self._generate_ollama_response(prompt)
        else:
            response_text = self._generate_openai_response(prompt)
            
        if not response_text:
            return None
        
        # Debug: Print raw response to understand the issue
        print(f"Raw response length: {len(response_text)}")
        print(f"Raw response preview: {response_text[:200]}...")
        
        # Extract JSON from response
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                print(f"No valid JSON found in response: {response_text[:100]}...")
                return None
                
            json_str = response_text[json_start:json_end]
            print(f"Extracted JSON: {json_str[:200]}...")
            dialogue_data = json.loads(json_str)
            
            return self._build_conversation_scene(
                dialogue_data, 
                chapter_num, 
                scene_id, 
                chunk_text
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {str(e)}")
            return None
    
    def _generate_ollama_response(self, prompt: str) -> Optional[str]:
        """Generate response using Ollama API."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,    # Low temperature for consistent JSON output
                "top_p": 0.7,          # Conservative token selection
                "num_predict": 1200,    # Reasonable output length
                "stop": ["Text:", "Example:", "\n\n"]  # Simple stop tokens
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=180)  # 3 minutes
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.RequestException as e:
            print(f"Ollama API error: {str(e)}")
            return None
    
    def _generate_openai_response(self, prompt: str) -> Optional[str]:
        """Generate response using OpenAI API."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting dialogue from fantasy novels. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return None
    
    def _build_conversation_scene(self, dialogue_data: Dict, chapter_num: int, 
                                scene_id: str, original_text: str) -> ConversationScene:
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
                chapter_number=chapter_num
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
    
    def get_character_index(self, scenes: List[ConversationScene]) -> Dict[str, List[CharacterDialogue]]:
        """
        Build CHARACTER INDEX: Group all dialogues by character for character agents.
        
        Args:
            scenes: List of conversation scenes
            
        Returns:
            Dictionary mapping character names to their dialogues
        """
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
    
    def get_scene_chunks(self, scenes: List[ConversationScene]) -> List[str]:
        """
        Get scene-based chunks for character-focused processing.
        Alternative chunking strategy to token-based chunking.
        """
        scene_chunks = []
        
        for scene in scenes:
            # Combine all dialogues in scene into a coherent chunk
            scene_text = f"Scene: {scene.setting}\n"
            scene_text += f"Participants: {', '.join(scene.participants)}\n\n"
            
            for dialogue in scene.dialogues:
                scene_text += f"{dialogue.character}: \"{dialogue.dialogue}\"\n"
                if dialogue.actions:
                    scene_text += f"Actions: {', '.join(dialogue.actions)}\n"
                scene_text += f"Emotion: {dialogue.emotion}\n\n"
            
            scene_chunks.append(scene_text)
        
        return scene_chunks
    
    def save_character_index(self, character_index: Dict, filepath: str = None):
        """Save the character index to JSON file with unique timestamp."""
        import datetime
        import os
        
        # Generate unique filename if not provided
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"./character_index_{timestamp}.json"
        else:
            # Add timestamp to provided filepath to make it unique
            base_name = os.path.splitext(filepath)[0]
            extension = os.path.splitext(filepath)[1] or '.json'
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{base_name}_{timestamp}{extension}"
        
        # Convert CharacterDialogue objects to dictionaries for JSON serialization
        serializable_index = {}
        
        for character, dialogues in character_index.items():
            serializable_index[character] = [
                {
                    "character": d.character,
                    "dialogue": d.dialogue,
                    "addressee": d.addressee,
                    "context": d.context,
                    "emotion": d.emotion,
                    "actions": d.actions,
                    "scene_id": d.scene_id,
                    "chapter_number": d.chapter_number
                }
                for d in dialogues
            ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_index, f, indent=2, ensure_ascii=False)
        
        print(f"Character index saved to {filepath}")

# Factory functions
def create_dialogue_extractor(model_type: str = "ollama", **kwargs) -> DialogueExtractor:
    """Factory function to create a dialogue extractor."""
    return DialogueExtractor(model_type=model_type, **kwargs)

def create_ollama_extractor(model_name: str = "llama3.1:8b-instruct-q4_0", prompt: str = None) -> DialogueExtractor:
    """Create an Ollama-based dialogue extractor."""
    return DialogueExtractor(model_type="ollama", model_name=model_name, prompt=prompt)

def create_openai_extractor(api_key: str = None, model_name: str = "gpt-4o-mini", prompt: str = None) -> DialogueExtractor:
    """Create an OpenAI-based dialogue extractor."""
    return DialogueExtractor(model_type="openai", model_name=model_name, api_key=api_key, prompt=prompt)

# Example usage
if __name__ == "__main__":
    from ChunkAccuracyTester import ChunkingAccuracyTester
    
    print("BookSouls Dialogue Extractor")
    print("=" * 60)
    
    # First, get chapters using existing chunker
    pdf_path = "./data/sample_books/j-r-r-tolkien-lord-of-the-rings-01-the-fellowship-of-the-ring-retail-pdf.pdf"
    chunker = ChunkingAccuracyTester(pdf_path)
    chapters = chunker.extract_chapters_from_pdf()
    
    if not chapters:
        print("ERROR: No chapters found")
        exit(1)
    
    # EXAMPLE 1: Using Ollama (Local Model) with default prompt
    print("\nExample 1: Ollama with default prompt")
    dialogue_extractor = create_ollama_extractor()
    
    # EXAMPLE 2: Using OpenAI (Cloud Model) with custom prompt
    # Uncomment to use OpenAI:
    # custom_prompt = '''Extract dialogue from fantasy text. Return JSON with:
    # {"dialogues": [{"speaker": "name", "dialogue": "text", "addressee": "who", 
    #                "emotion": "mood", "actions": [], "context": "situation"}],
    #  "scene_setting": "description", "participants": ["names"]}
    # Text: {text_chunk}'''
    # dialogue_extractor = create_openai_extractor(prompt=custom_prompt)
    
    # EXAMPLE 3: Using built-in advanced prompt with Ollama
    # from prompts import ADVANCED_DIALOGUE_EXTRACTION
    # dialogue_extractor = create_ollama_extractor(prompt=ADVANCED_DIALOGUE_EXTRACTION)
    
    # Extract character-focused dialogues (function will handle token chunking internally)
    scenes = dialogue_extractor.extract_dialogues_from_chapters(chunker, chapters[:2])  # Test with first 2 chapters
    
    if scenes:
        print(f"\nSCENE EXTRACTION RESULTS:")
        print(f"Scenes extracted: {len(scenes)}")
        
        # Build CHARACTER INDEX
        character_index = dialogue_extractor.get_character_index(scenes)
        
        print(f"\nCHARACTER INDEX:")
        for character, dialogues in character_index.items():
            print(f"  {character}: {len(dialogues)} dialogues")
        
        # Get scene-based chunks
        scene_chunks = dialogue_extractor.get_scene_chunks(scenes)
        
        print(f"\nREADY FOR CHARACTER AGENTS:")
        print(f"Scene-based chunks: {len(scene_chunks)}")
        print(f"Characters with dialogues: {len(character_index)}")
        print(f"✨ CHARACTER INDEX ready for BookSouls agents!")
        
        # Save character index
        dialogue_extractor.save_character_index(character_index, "./data/outputs/character_index.json")
        
    else:
        print("ERROR: No dialogues extracted")