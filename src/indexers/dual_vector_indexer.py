"""
DualVectorIndexer - Optimized Vector Stores for BookSouls Agents

Creates two specialized ChromaDB collections:
1. Narrative Store - For Author Agent (strategic, thematic retrieval)
2. Dialogue Store - For Character Agents (character-focused, dialogue retrieval)

Each store uses optimized embedding strategies for their specific use case.
"""

import chromadb
from chromadb.config import Settings
from typing import Dict, Any, Optional, List
import json
import time
import datetime
import os

# Import our chunkers and config
from ..chunkers.chapter_chunker import SectionIndex
from ..chunkers.dialogue_chunker import DialogueIndex
from .config import IndexerConfig, get_default_config, EmbeddingFunction




class DualVectorIndexer:
    """
    Manages dual vector stores optimized for BookSouls agents.
    
    - Narrative Store: Optimized for Author Agent's omniscient perspective
    - Dialogue Store: Optimized for Character Agents' character-focused retrieval
    """
    
    def __init__(self, config: IndexerConfig = None):
        """
        Initialize dual vector stores.
        
        Args:
            config: IndexerConfig instance, defaults to get_default_config()
        """
        self.config = config or get_default_config()
        self.base_persist_dir = self.config.base_persist_dir
        self.narrative_collection_name = self.config.narrative_collection
        self.dialogue_collection_name = self.config.dialogue_collection
        
        # Ensure directories exist
        os.makedirs(self.base_persist_dir, exist_ok=True)
        os.makedirs(f"{self.base_persist_dir}/narrative", exist_ok=True)
        os.makedirs(f"{self.base_persist_dir}/dialogue", exist_ok=True)
        
        # Initialize ChromaDB clients
        self._init_clients()
        
        # Store metadata
        self.indexing_metadata = {
            'created_at': datetime.datetime.now().isoformat(),
            'narrative_store': f"{self.base_persist_dir}/narrative",
            'dialogue_store': f"{self.base_persist_dir}/dialogue"
        }
    
    def _init_clients(self):
        """Initialize separate ChromaDB clients for each store."""
        # Narrative Store - Optimized for semantic/thematic search
        self.narrative_client = chromadb.PersistentClient(
            path=f"{self.base_persist_dir}/narrative",
            settings=Settings(
                anonymized_telemetry=self.config.anonymized_telemetry,
                allow_reset=self.config.allow_reset
            )
        )
        
        # Dialogue Store - Optimized for character/dialogue search  
        self.dialogue_client = chromadb.PersistentClient(
            path=f"{self.base_persist_dir}/dialogue",
            settings=Settings(
                anonymized_telemetry=self.config.anonymized_telemetry,
                allow_reset=self.config.allow_reset
            )
        )
        
        # Get or create collections with embedding functions
        self.narrative_collection = self.narrative_client.get_or_create_collection(
            name=self.narrative_collection_name,
            embedding_function=self._get_embedding_function(self.config.narrative_embedding),
            metadata={"description": "Narrative chunks for Author Agent omniscient retrieval"}
        )
        
        self.dialogue_collection = self.dialogue_client.get_or_create_collection(
            name=self.dialogue_collection_name,
            embedding_function=self._get_embedding_function(self.config.dialogue_embedding),
            metadata={"description": "Dialogue chunks for Character Agent focused retrieval"}
        )
    
    def index_narrative_chunks(self, section_index: SectionIndex) -> Dict[str, Any]:
        """
        Index narrative chunks optimized for Author Agent retrieval.
        
        Strategy:
        - Enhanced section chunks with thematic/entity context
        - Section-level indexing only (no chapter-level for now)
        - Metadata includes themes, entities, semantic types
        """
        print("Indexing narrative chunks for Author Agent...")
        start_time = time.time()
        
        documents = []
        metadatas = []
        ids = []
        
        # # COMMENTED OUT: Chapter-level indexing (may add separate collection later)
        # for chapter in chapter_index.chapters:
        #     # Enhanced chapter content with metadata
        #     enhanced_content = self._create_narrative_enhanced_content(chapter, is_chapter=True)
        #     
        #     documents.append(enhanced_content)
        #     metadatas.append({
        #         "type": "chapter",
        #         "chapter_number": chapter.chapter_number,
        #         "chapter_title": chapter.chapter_title,
        #         "entities": json.dumps(chapter.entities),
        #         "themes": json.dumps(chapter.themes),
        #         "token_count": chapter.token_count,
        #         "summary": chapter.summary,
        #         "start_page": chapter.start_page,
        #         "end_page": chapter.end_page
        #     })
        #     ids.append(f"chapter_{chapter.chapter_number}")
        
        # Index section-level chunks only
        for section in section_index.sections:
            enhanced_content = self._create_narrative_enhanced_content(section, is_chapter=False)
            
            documents.append(enhanced_content)
            metadatas.append({
                "type": "section",
                "section_id": section.section_id,
                "chapter_number": section.chapter_number,
                "section_index": section.section_index,
                "semantic_type": section.semantic_type,
                "entities": json.dumps(section.entities),
                "themes": json.dumps(section.themes),
                "token_count": section.token_count,
                "parent_chapter_id": section.parent_chapter_id
            })
            ids.append(section.section_id)
        
        # Add to narrative collection
        self.narrative_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        processing_time = time.time() - start_time
        
        result = {
            'total_chunks': len(documents),
            'section_chunks': len(section_index.sections),
            'processing_time': processing_time,
            'collection_name': self.narrative_collection_name
        }
        
        print(f"Narrative indexing complete: {result['total_chunks']} chunks in {processing_time:.2f}s")
        return result
    
    def index_dialogue_chunks(self, dialogue_index: DialogueIndex) -> Dict[str, Any]:
        """
        Index dialogue chunks optimized for Character Agent retrieval.
        
        Strategy:
        - Speaker-focused enhanced content
        - Emotional and action context preserved
        - Character-specific metadata for targeted retrieval
        """
        print("Indexing dialogue chunks for Character Agents...")
        start_time = time.time()
        
        documents = []
        metadatas = []
        ids = []
        
        # Index scene-level dialogue chunks
        for scene in dialogue_index.scenes:
            # Create scene-based chunk
            enhanced_content = self._create_dialogue_enhanced_content(scene)
            
            documents.append(enhanced_content)
            metadatas.append({
                "type": "scene",
                "scene_id": scene.scene_id,
                "chapter_number": scene.chapter_number,
                "participants": json.dumps(scene.participants),
                "setting": scene.setting,
                "dialogue_count": len(scene.dialogues)
            })
            ids.append(scene.scene_id)
        
        # Index individual character dialogues for precise character retrieval
        for _character, dialogues in dialogue_index.by_character.items():
            for i, dialogue in enumerate(dialogues):
                enhanced_content = self._create_character_dialogue_content(dialogue)
                
                documents.append(enhanced_content)
                metadatas.append({
                    "type": "character_dialogue",
                    "character": dialogue.character,
                    "addressee": dialogue.addressee,
                    "emotion": dialogue.emotion,
                    "chapter_number": dialogue.chapter_number,
                    "scene_id": dialogue.scene_id,
                    "section_id": dialogue.section_id,
                    "actions": json.dumps(dialogue.actions)
                })
                ids.append(f"{dialogue.character}_{dialogue.scene_id}_{i}")
        
        # Index character profiles for semantic search
        for character, profiles in dialogue_index.character_profiles.items():
            for profile in profiles:
                # Use the new to_json_string method to get JSON representation
                profile_json = profile.to_json_string()
                
                documents.append(profile_json)
                # Extract personality traits text for metadata
                if profile.personality_traits:
                    if isinstance(profile.personality_traits[0], dict):
                        personality_text = ', '.join([trait.get('trait', '') for trait in profile.personality_traits if trait.get('trait')])
                    else:
                        personality_text = ', '.join(profile.personality_traits)
                else:
                    personality_text = ''
                
                # Extract motivations text for metadata
                if profile.motivations:
                    if isinstance(profile.motivations[0], dict):
                        motivations_text = ', '.join([mot.get('motivation', '') or mot.get('goal', '') for mot in profile.motivations])
                    else:
                        motivations_text = ', '.join(profile.motivations)
                else:
                    motivations_text = ''
                
                metadatas.append({
                    "type": "character_profile",
                    "character": profile.name,
                    "chapter_number": profile.chapter_number,
                    "personality_traits": personality_text,
                    "motivations": motivations_text,
                    "emotional_state": profile.emotional_state,
                    "dialogue_count": profile.dialogue_count,
                })
                ids.append(f"profile_{profile.name}_ch{profile.chapter_number}")
        
        # Add to dialogue collection
        self.dialogue_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        processing_time = time.time() - start_time
        
        character_profile_count = sum(len(profiles) for profiles in dialogue_index.character_profiles.values())
        
        result = {
            'total_chunks': len(documents),
            'scene_chunks': len(dialogue_index.scenes),
            'character_dialogue_chunks': len(documents) - len(dialogue_index.scenes) - character_profile_count,
            'character_profile_chunks': character_profile_count,
            'characters_indexed': len(dialogue_index.characters),
            'processing_time': processing_time,
            'collection_name': self.dialogue_collection_name
        }
        
        print(f"Dialogue indexing complete: {result['total_chunks']} chunks in {processing_time:.2f}s")
        return result
    
    def _create_narrative_enhanced_content(self, chunk, is_chapter: bool = True) -> str:
        """Create enhanced content for narrative retrieval."""
        if is_chapter:
            # Chapter-level enhancement
            enhanced = f"Chapter {chunk.chapter_number}: {chunk.chapter_title}\n"
            enhanced += f"Summary: {chunk.summary}\n\n"
            
            if chunk.entities:
                enhanced += f"Key Characters/Entities: {', '.join(chunk.entities[:5])}\n"
            
            if chunk.themes:
                enhanced += f"Themes: {', '.join(chunk.themes)}\n"
            
            enhanced += f"\n--- Chapter Content ---\n{chunk.content}"
            
        else:
            # Section-level enhancement
            enhanced = f"Chapter {chunk.chapter_number} - Section {chunk.section_index}\n"
            enhanced += f"[{chunk.semantic_type.upper()}]\n"
            
            if chunk.entities:
                enhanced += f"Entities: {', '.join(chunk.entities)}\n"
                
            if chunk.themes:
                enhanced += f"Themes: {', '.join(chunk.themes)}\n"
            
            enhanced += f"\n--- Section Content ---\n{chunk.content}"
        
        return enhanced
    
    def _create_dialogue_enhanced_content(self, scene) -> str:
        """Create enhanced content for scene-based dialogue retrieval."""
        enhanced = f"Scene: {scene.setting}\n" if scene.setting else ""
        enhanced += f"Participants: {', '.join(scene.participants)}\n\n" if scene.participants else ""
        
        for dialogue in scene.dialogues:
            enhanced += f"[{dialogue.character}]: \"{dialogue.dialogue}\"\n"
            if dialogue.actions:
                enhanced += f"Actions: {', '.join(dialogue.actions)}\n"
            enhanced += f"Emotion: {dialogue.emotion}\n"
            if dialogue.addressee != "Unknown":
                enhanced += f"Speaking to: {dialogue.addressee}\n"
            enhanced += "\n"
        
        return enhanced
    
    def _create_character_dialogue_content(self, dialogue) -> str:
        """Create enhanced content for individual character dialogue retrieval."""
        enhanced = f"[{dialogue.character}]: \"{dialogue.dialogue}\"\n\n"
        enhanced += f"Context: Chapter {dialogue.chapter_number}\n"
        enhanced += f"Speaking to: {dialogue.addressee}\n"
        enhanced += f"Emotion: {dialogue.emotion}\n"
        
        if dialogue.actions:
            enhanced += f"Actions: {', '.join(dialogue.actions)}\n"
        
        if dialogue.context:
            enhanced += f"Scene Context: {dialogue.context}\n"
        
        return enhanced
    
    def _get_embedding_function(self, embedding_config):
        """Get ChromaDB embedding function based on configuration."""
        if embedding_config.function_type == EmbeddingFunction.DEFAULT:
            return None  # Use ChromaDB's default
        
        elif embedding_config.function_type in [EmbeddingFunction.OPENAI_ADA_002, 
                                               EmbeddingFunction.OPENAI_3_SMALL, 
                                               EmbeddingFunction.OPENAI_3_LARGE]:
            try:
                from chromadb.utils import embedding_functions
                model_name = embedding_config.function_type.value
                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=embedding_config.api_key,
                    model_name=model_name,
                    **embedding_config.model_kwargs
                )
            except ImportError:
                print("Warning: openai not available, using default")
                return None
        
        else:
            print(f"Warning: Unknown embedding function {embedding_config.function_type}, using default")
            return None
    
    def query_narrative(self, query: str, n_results: int = None, 
                       where: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Query narrative store for Author Agent.
        
        Args:
            query: Search query for thematic/narrative content
            n_results: Number of results to return
            where: Optional metadata filters
        """
        if n_results is None:
            n_results = self.config.narrative_query.n_results
            
        results = self.narrative_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=self.config.narrative_query.include
        )
        
        return {
            'query': query,
            'results': results,
            'store_type': 'narrative'
        }
    
    def query_dialogue(self, query: str, n_results: int = None,
                      character: Optional[str] = None,
                      where: Optional[Dict] = None,
                      # Extended filtering parameters
                      dialogue_type: Optional[str] = None,  # "scene", "character_dialogue", "character_profile"
                      addressee: Optional[str] = None,
                      emotion: Optional[str] = None,
                      chapter_number: Optional[int] = None,
                      scene_id: Optional[str] = None,
                      setting: Optional[str] = None,
                      participants: Optional[List[str]] = None,
                      personality_traits: Optional[List[str]] = None,
                      emotional_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced query dialogue store with comprehensive filtering.
        
        Args:
            query: Search query for character/dialogue content
            n_results: Number of results to return
            character: Optional specific character filter
            where: Optional metadata filters (will be merged with other filters)
            
            # Extended filters:
            dialogue_type: Filter by type ("scene", "character_dialogue", "character_profile")
            addressee: Who the character is speaking to
            emotion: Emotional state of the dialogue
            chapter_number: Filter by chapter
            scene_id: Filter by specific scene
            setting: Scene location/setting (for scene queries)
            participants: List of characters (for scene queries)
            personality_traits: List of traits (for profile queries)
            emotional_state: Character's emotional state (for profile queries)
        """
        if n_results is None:
            n_results = self.config.dialogue_query.n_results
        
        # Build comprehensive where filter using ChromaDB operators
        conditions = []
        
        # Add existing where conditions (wrap if needed)
        if where:
            # If where already has operators, use as-is, otherwise wrap with $eq
            if any(key.startswith('$') for key in where.keys()):
                conditions.append(where)
            else:
                # Convert simple dict to operator format
                for key, value in where.items():
                    conditions.append({key: {"$eq": value}})
        
        # Add dialogue type filter
        if dialogue_type:
            conditions.append({"type": {"$eq": dialogue_type}})
        
        # Add character filter  
        if character:
            conditions.append({"character": {"$eq": character}})
            
        # Add specific filters
        if addressee:
            conditions.append({"addressee": {"$eq": addressee}})
        if emotion:
            conditions.append({"emotion": {"$eq": emotion}})
        if chapter_number:
            conditions.append({"chapter_number": {"$eq": chapter_number}})
        if scene_id:
            conditions.append({"scene_id": {"$eq": scene_id}})
        if emotional_state:
            conditions.append({"emotional_state": {"$eq": emotional_state}})
        
        # Construct final where clause
        if len(conditions) == 0:
            filter_dict = None
        elif len(conditions) == 1:
            # For single condition, use the condition directly
            filter_dict = conditions[0]
        else:
            # For multiple conditions, use $and operator
            filter_dict = {"$and": conditions}
        
        # Enhance query with additional context
        query_parts = [query]
        
        # Add setting to query for better semantic matching
        if setting:
            query_parts.append(f"setting {setting}")
            
        # Add participants to query for scene searches
        if participants:
            query_parts.extend([f"participant {p}" for p in participants])
            
        # Add personality traits to query for profile searches
        if personality_traits:
            query_parts.extend(personality_traits)
            
        # Add addressee to query for better matching
        if addressee and character:
            query_parts.append(f"{character} speaking to {addressee}")
            
        # Add emotion to query for better matching
        if emotion:
            query_parts.append(f"emotion {emotion}")
        
        enhanced_query = " ".join(query_parts)
        
        # Debug: Print filter structure
        print(f"DEBUG: Enhanced query: {enhanced_query}")
        print(f"DEBUG: Filter dict: {filter_dict}")
        print(f"DEBUG: Number of conditions: {len(conditions) if 'conditions' in locals() else 'N/A'}")
        
        try:
            results = self.dialogue_collection.query(
                query_texts=[enhanced_query],
                n_results=n_results,
                where=filter_dict,
                include=self.config.dialogue_query.include
            )
        except Exception as e:
            print(f"DEBUG: ChromaDB query failed with filter: {filter_dict}")
            print(f"DEBUG: Error: {str(e)}")
            # Fallback: try without filters
            print("DEBUG: Retrying without filters...")
            results = self.dialogue_collection.query(
                query_texts=[enhanced_query],
                n_results=n_results,
                where=None,
                include=self.config.dialogue_query.include
            )
        
        return {
            'query': enhanced_query,
            'original_query': query,
            'filters_applied': filter_dict,
            'character_filter': character,
            'results': results,
            'store_type': 'dialogue'
        }
    
    def get_character_dialogues(self, character: str, addressee:Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get all dialogues for a specific character."""
        return self.query_dialogue(
            query=f"{character}: all dialogues",
            character=character,
            addressee=addressee,
            dialogue_type="character_dialogue",
            n_results=limit
        )
    
    def get_chapter_content(self, chapter_number: int) -> Dict[str, Any]:
        """Get all content for a specific chapter."""
        return self.query_narrative(
            query=f"chapter {chapter_number}",
            where={"chapter_number": chapter_number}
        )
    
    def get_narrative_content(self, theme: str, n_results: int = 5) -> Dict[str, Any]:
        """Search for narrative content"""
        return self.query_narrative(
            query=f"theme {theme}",
            n_results=n_results
        )
    
    def query_character_profiles(self,character: str, n_results: int = 5) -> Dict[str, Any]:
        """Search character profiles by traits, motivations, etc."""
        return self.query_dialogue(
            query=f'{character} character profile traits personality',
            character=character,
            dialogue_type="character_profile",
            n_results=n_results
        )
    
    def reset_stores(self):
        """Reset both vector stores (useful for development/testing)."""
        print("Resetting both vector stores...")
        self.narrative_client.reset()
        self.dialogue_client.reset()
        self._init_clients()
        print("Vector stores reset complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for both stores."""
        narrative_count = self.narrative_collection.count()
        dialogue_count = self.dialogue_collection.count()
        
        return {
            'narrative_store': {
                'collection_name': self.narrative_collection_name,
                'document_count': narrative_count,
                'path': f"{self.base_persist_dir}/narrative"
            },
            'dialogue_store': {
                'collection_name': self.dialogue_collection_name,
                'document_count': dialogue_count,
                'path': f"{self.base_persist_dir}/dialogue"
            },
            'total_documents': narrative_count + dialogue_count,
            'indexing_metadata': self.indexing_metadata
        }


# Factory functions
def create_dual_indexer(config: IndexerConfig = None) -> DualVectorIndexer:
    """Factory function to create a dual vector indexer."""
    return DualVectorIndexer(config=config)

def create_dual_indexer_with_dir(base_persist_dir: str) -> DualVectorIndexer:
    """Factory function to create a dual vector indexer with custom directory."""
    config = get_default_config()
    config.base_persist_dir = base_persist_dir
    return DualVectorIndexer(config=config)