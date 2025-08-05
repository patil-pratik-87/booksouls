"""
Character Profile Extractor - Simplified version that extracts and builds character personas from indexed data.

Integrates with DualVectorIndexer to gather character information
and builds CharacterPersona objects for use with CharacterAgent.
"""

from typing import Dict, List, Any, Optional
import json

from .character_agent import CharacterPersona
from ..indexers.dual_vector_indexer import DualVectorIndexer
from ..chunkers.dialogue_chunker import CharacterProfile


class CharacterExtractor:
    """
    Simplified character extractor that builds personas from indexed data.
    """
    
    def __init__(self, indexer: DualVectorIndexer):
        """
        Initialize extractor with indexer access.
        
        Args:
            indexer: DualVectorIndexer instance for querying character data
        """
        self.indexer = indexer
    
    def extract_character_persona(self, character_name: str) -> Optional[CharacterPersona]:
        """
        Extract character persona from indexed data.
        
        Args:
            character_name: Name of character to extract
            
        Returns:
            CharacterPersona object or None if character not found
        """
        try:
            # Get character data
            data = self._gather_character_data(character_name)
            
            if not data:
                return None
            
            # Build simplified persona
            return self._build_persona(character_name, data)
            
        except Exception as e:
            print(f"Error extracting character persona for {character_name}: {str(e)}")
            return None
    
    def _gather_character_data(self, character_name: str) -> Dict[str, Any]:
        """Gather character data from vector store."""
        data = {}
        
        try:
            # Get character dialogues
            dialogues_result = self.indexer.get_character_dialogues(character_name, limit=15)
            data['dialogues'] = self._format_results(dialogues_result)
            
            # Get character profiles
            profiles_result = self.indexer.query_character_profiles(character=character_name, n_results=1)
            data['profiles'] = self._format_results(profiles_result)
            
            # Get narrative context
            narrative_result = self.indexer.query_narrative(
                f"{character_name} character background in brief", n_results=2
            )
            data['narrative_context'] = self._format_results(narrative_result)
            
        except Exception as e:
            print(f"Warning: Error gathering character data: {str(e)}")
        
        return data
    
    def _format_results(self, query_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format query results into simple structure."""
        if not query_result or 'results' not in query_result:
            return []
        
        results = query_result['results']
        documents = results['documents'][0] if 'documents' in results and results['documents'] else []
        metadatas = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else []
        ids = results['ids'][0] if 'ids' in results and results['ids'] else []
        
        formatted = []
        for i, doc in enumerate(documents):
            result = {
                'document': doc,
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'id': ids[i] if i < len(ids) else f'doc_{i}'
            }
            formatted.append(result)
        
        return formatted
    
    def _build_persona(self, character_name: str, data: Dict[str, Any]) -> CharacterPersona:
        """Build simplified CharacterPersona from gathered data."""
        
        # Extract core attributes using simplified methods
        personality_traits = self._extract_core_attributes(data, 'personality_traits')
        motivations = self._extract_core_attributes(data, 'motivations')
        # core_beliefs = self._extract_core_attributes(data, 'core_beliefs')
        emotional_state = self._extract_core_attributes(data, 'emotional_state')
        speech_style = self._extract_core_attributes(data, 'speech_style')
        relationships = self._extract_core_attributes(data, 'key_relationships')
        
        
        return CharacterPersona(
            name=character_name,
            personality_traits=personality_traits,
            motivations=motivations,
            speech_style=speech_style,
            relationships=relationships,
            emotional_state=emotional_state,
        )
    
    def _extract_core_attributes(self, data: Dict[str, Any], attribute_name: str) -> List[str]:
        """Extract core attributes (personality_traits, motivations, core_beliefs) from character profiles."""
        attributes = []

        # Extract from character profiles document field
        for result in data.get('profiles', []):
            document = result.get('document', '')
            if document:
                try:
                    profile_data = json.loads(document)
                    if attribute_name in profile_data:
                        attribute_data = profile_data[attribute_name]
                        attributes.append(attribute_data)
                    else:
                        raise ValueError(f"Attribute {attribute_name} is not a list")
                except (json.JSONDecodeError, TypeError):
                    continue
                
            return attributes
    
    
    def get_available_characters(self) -> List[str]:
        """Get list of all available characters from the indexer."""
        try:
            characters = set()
            results = self.indexer.query_character_profiles("", n_results=100)
            
            if 'results' in results and 'metadatas' in results['results']:
                metadatas = results['results']['metadatas'][0]
                for metadata in metadatas:
                    if 'character' in metadata:
                        characters.add(metadata['character'].lower())

            return sorted(list(characters))
            
        except Exception as e:
            print(f"Error getting available characters: {str(e)}")
            return []
