"""
ChapterChunker - Narrative Index Generation for BookSouls Author Agent

Creates semantically chunked text optimized for the Author agent's omniscient view.
Focuses on preserving narrative flow, world-building details, and chapter structure.
"""

import time
from typing import List, Dict, Any
from dataclasses import dataclass
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import datetime
import os

from src.chunkers.config.config import ChapterChunkerConfig
from src.prompts.chapter_chunker_prompts import (
    CHAPTER_SUMMARY_PROMPT,
    SEMANTIC_CLASSIFICATION_PROMPT,
    THEME_EXTRACTION_PROMPT,
    ENTITY_EXTRACTION_PROMPT
)


@dataclass
class SectionChunk:
    """Represents a granular section within a chapter for detailed narrative search."""
    section_id: str      # "ch1_sec3"
    content: str         # 800-1200 tokens
    chapter_number: int
    section_index: int   # 0, 1, 2, 3...
    token_count: int
    word_count: int
    semantic_type: str   # 'narrative', 'dialogue', 'description', 'action'
    entities: List[str]  # Section-specific entities
    themes: List[str]    # Section-specific themes
    parent_chapter_id: str  # "chapter_1"


@dataclass
class ChapterChunk:
    """Represents a complete chapter for high-level strategic search."""
    chapter_id: str      # "chapter_1"  
    content: str         # Full chapter text
    chapter_sections: List[SectionChunk]  # Granular sections within chapter
    chapter_number: int
    chapter_title: str
    start_page: int
    end_page: int
    token_count: int
    word_count: int
    summary: str         # LLM-generated chapter summary
    entities: List[str]  # All entities in chapter
    themes: List[str]    # High-level chapter themes


@dataclass
class ChapterIndex:
    """Chapter-level index for strategic, high-level search."""
    chapters: List[ChapterChunk]
    total_chapters: int
    total_tokens: int
    entities: Dict[str, int]  # Entity frequency across all chapters
    themes: Dict[str, int]    # Theme frequency across all chapters
    metadata: Dict[str, Any]


@dataclass  
class SectionIndex:
    """Section-level index for detailed, granular search."""
    sections: List[SectionChunk]  # Flattened sections from all chapters
    total_sections: int
    total_tokens: int
    chapters_covered: List[int]
    entities: Dict[str, int]  # Entity frequency across all sections
    themes: Dict[str, int]    # Theme frequency across all sections
    metadata: Dict[str, Any]


class ChapterChunker:
    """
    Creates hierarchical Chapter and Section indexes for BookSouls Author Agent.
    
    Optimized for:
    - Dual-level search: Strategic (chapter) + Detailed (section)
    - Complete narrative understanding
    - World-building preservation
    - Omniscient perspective
    - Semantic coherence
    
    Configuration:
    The chunker is configured via ChapterChunkerConfig which controls:
    - LLM settings: model_name, temperature, top_p, max_tokens, request_timeout
    - Section filtering: min_section_tokens (skips micro-chunks)
    - Semantic types: which content types to recognize (narrative, dialogue, etc.)
    - Logging: verbose flag for detailed processing output
    """
    
    def __init__(self, cfg: ChapterChunkerConfig = ChapterChunkerConfig()):
        """
        Initialize hierarchical chunker.
        
        Note: Chunking is already done by PDFChapterExtractor, so we just need
        tokenizer for token counting in analysis.
        """
        # Initialize tokenizer for token counting
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.cfg = cfg
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
    
    def create_hierarchical_indexes(self, chapters: List) -> tuple[ChapterIndex, SectionIndex]:
        """
        Create both Chapter and Section indexes from extracted chapters.
        
        Args:
            chapters: List of ChapterChunk objects from PDF extractor
            
        Returns:
            Tuple of (ChapterIndex, SectionIndex) for dual-level search
        """
        if self.cfg.verbose:
            print(f"Creating hierarchical indexes from {len(chapters)} chapters...")
        start_time = time.time()
        
        # Storage for both indexes
        processed_chapters = []
        all_sections = []
        
        # Entity and theme frequency tracking
        chapter_entities = {}
        chapter_themes = {}
        section_entities = {}
        section_themes = {}
        
        total_chapter_tokens = 0
        total_section_tokens = 0
        
        for chapter in chapters:
            if self.cfg.verbose:
                print(f"Processing Chapter {chapter.chapter_number}: {chapter.chapter_title}")
            
            # Use existing chunks from PDFChapterExtractor (already split with RecursiveCharacterTextSplitter)
            existing_chunks = chapter.chunks
            chapter_sections = []
            
            for i, section_content in enumerate(existing_chunks):
                # Skip very small sections using config value
                token_count = self._count_tokens(section_content)
                if token_count < self.cfg.min_section_tokens:
                    continue
                
                # Analyze section for semantic metadata using configured LLM
                entities = self._extract_entities_llm(section_content)
                semantic_type = self._classify_semantic_type_llm(section_content)
                themes = self._extract_themes_llm(section_content)
                
                # Create section chunk
                section_chunk = SectionChunk(
                    section_id=f"ch{chapter.chapter_number}_sec{i}",
                    content=section_content,
                    chapter_number=chapter.chapter_number,
                    section_index=i,
                    token_count=token_count,
                    word_count=len(section_content.split()),
                    semantic_type=semantic_type,
                    entities=entities,
                    themes=themes,
                    parent_chapter_id=f"chapter_{chapter.chapter_number}"
                )
                
                chapter_sections.append(section_chunk)
                all_sections.append(section_chunk)
                total_section_tokens += token_count
                
                # Update section-level entity and theme frequencies
                for entity in entities:
                    section_entities[entity] = section_entities.get(entity, 0) + 1
                for theme in themes:
                    section_themes[theme] = section_themes.get(theme, 0) + 1
            
            # Aggregate chapter-level metadata from sections
            chapter_all_entities = []
            chapter_all_themes = []
            for section in chapter_sections:
                chapter_all_entities.extend(section.entities)
                chapter_all_themes.extend(section.themes)
            
            # Remove duplicates and get unique entities/themes for chapter
            unique_chapter_entities = list(set(chapter_all_entities))
            unique_chapter_themes = list(set(chapter_all_themes))
            
            # Generate chapter summary using configured LLM
            chapter_summary = self._generate_chapter_summary_llm(chapter.content)
            
            # Create enhanced chapter chunk
            enhanced_chapter = ChapterChunk(
                chapter_id=f"chapter_{chapter.chapter_number}",
                content=chapter.content,
                chapter_sections=chapter_sections,
                chapter_number=chapter.chapter_number,
                chapter_title=chapter.chapter_title,
                start_page=chapter.start_page,
                end_page=chapter.end_page,
                token_count=chapter.token_count,
                word_count=chapter.word_count,
                summary=chapter_summary,
                entities=unique_chapter_entities,
                themes=unique_chapter_themes
            )
            
            processed_chapters.append(enhanced_chapter)
            total_chapter_tokens += chapter.token_count
            
            # Update chapter-level entity and theme frequencies
            for entity in unique_chapter_entities:
                chapter_entities[entity] = chapter_entities.get(entity, 0) + 1
            for theme in unique_chapter_themes:
                chapter_themes[theme] = chapter_themes.get(theme, 0) + 1
            
            if self.cfg.verbose:
                print(f"   Chapter {chapter.chapter_number}: {len(chapter_sections)} sections, {len(unique_chapter_themes)} themes")
        
        processing_time = time.time() - start_time
        
        # Create Chapter Index
        chapter_index = ChapterIndex(
            chapters=processed_chapters,
            total_chapters=len(processed_chapters),
            total_tokens=total_chapter_tokens,
            entities=chapter_entities,
            themes=chapter_themes,
            metadata={
                'processing_time': processing_time,
                'created_at': datetime.datetime.now().isoformat(),
                'avg_tokens_per_chapter': total_chapter_tokens / len(processed_chapters) if processed_chapters else 0,
                'avg_sections_per_chapter': len(all_sections) / len(processed_chapters) if processed_chapters else 0,
                'config_used': {
                    'model_name': self.cfg.model_name,
                    'min_section_tokens': self.cfg.min_section_tokens,
                    'semantic_types': self.cfg.semantic_types
                }
            }
        )
        
        # Create Section Index
        section_index = SectionIndex(
            sections=all_sections,
            total_sections=len(all_sections),
            total_tokens=total_section_tokens,
            chapters_covered=[ch.chapter_number for ch in processed_chapters],
            entities=section_entities,
            themes=section_themes,
            metadata={
                'processing_time': processing_time,
                'chunking_source': 'PDFChapterExtractor',
                'created_at': datetime.datetime.now().isoformat(),
                'avg_tokens_per_section': total_section_tokens / len(all_sections) if all_sections else 0,
                'config_used': {
                    'model_name': self.cfg.model_name,
                    'min_section_tokens': self.cfg.min_section_tokens,
                    'semantic_types': self.cfg.semantic_types
                }
            }
        )
        
        if self.cfg.verbose:
            print(f"Created hierarchical indexes:")
            print(f"   Chapter Index: {len(processed_chapters)} chapters, {total_chapter_tokens:,} tokens")
            print(f"   Section Index: {len(all_sections)} sections, {total_section_tokens:,} tokens")
            print(f"   Found {len(chapter_entities)} unique entities, {len(chapter_themes)} unique themes")
            print(f"   Processing time: {processing_time:.2f}s")
        
        return chapter_index, section_index
    
    
    
    def _generate_chapter_summary_llm(self, chapter_content: str) -> str:
        """Generate chapter summary using configured LLM."""
        prompt = CHAPTER_SUMMARY_PROMPT.format(chapter_text=chapter_content)
        
        return self._call_llm(prompt, max_tokens=self.cfg.max_tokens)
    
    def _classify_semantic_type_llm(self, text: str) -> str:
        """Use configured LLM to classify semantic type of text chunk."""
        prompt = SEMANTIC_CLASSIFICATION_PROMPT.format(
            semantic_types=', '.join(self.cfg.semantic_types),
            text=text
        )
        
        result = self._call_llm(prompt, max_tokens=5)
        return result.lower().strip() if result.lower().strip() in self.cfg.semantic_types else self.cfg.semantic_types[0]
    
    def _extract_themes_llm(self, text: str) -> List[str]:
        """Extract themes using configured LLM analysis."""
        prompt = THEME_EXTRACTION_PROMPT.format(text=text)
        
        result = self._call_llm(prompt, max_tokens=50)
        if result:
            themes = [theme.strip().lower() for theme in result.split(',')]
            return themes[:3]  # Limit to 3 themes
        return []
    
    def _extract_entities_llm(self, text: str) -> List[str]:
        """Extract named entities using configured LLM."""
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)
        
        result = self._call_llm(prompt, max_tokens=100)
        if result:
            entities = [entity.strip() for entity in result.split(',')]
            return entities[:8]  # Limit to 8 entities
        return []
    
    def _call_llm(self, prompt: str, max_tokens: int = None) -> str:
        """
        Call configured LLM for semantic analysis.
        max_tokens: Maximum number of tokens the LLM can generate (uses config default if None)
        """
        if max_tokens is None:
            max_tokens = self.cfg.max_tokens
            
        try:
            import openai
            import os
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model=self.cfg.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing literature. Provide concise, accurate responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.cfg.temperature,
                top_p=self.cfg.top_p,
                timeout=self.cfg.request_timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            if self.cfg.verbose:
                print(f"Warning: {self.cfg.model_name} call failed: {str(e)}")
            return ""  # Fallback to empty result
 # Example usage inside an LLM helper
    async def _call_llm_async(self, messages: list[str]) -> str:
        """Call configured LLM asynchronously for semantic analysis."""
        try:
            import openai
            import os
            
            # Initialize OpenAI async client
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            resp = await client.chat.completions.create(
                model=self.cfg.model_name,
                messages=messages,
                max_tokens=self.cfg.max_tokens,
                temperature=self.cfg.temperature,
                top_p=self.cfg.top_p,
                timeout=self.cfg.request_timeout
            )
            return resp.choices[0].message.content.strip()
            
        except Exception as e:
            if self.cfg.verbose:
                print(f"Warning: Async {self.cfg.model_name} call failed: {str(e)}")
            return ""  # Fallback to empty result
        
    def get_chapter_chunks(self, chapter_index: ChapterIndex) -> List[str]:
        """
        Get chapter-level text chunks ready for vector database indexing.
        
        Returns:
            List of enhanced chapter chunks optimized for strategic search
        """
        chunks = []
        
        for chapter in chapter_index.chapters:
            # Enhance chapter with metadata for better retrieval
            enhanced_chunk = f"Chapter {chapter.chapter_number}: {chapter.chapter_title}\n"
            enhanced_chunk += f"Summary: {chapter.summary}\n"
            
            if chapter.entities:
                enhanced_chunk += f"Characters/Entities: {', '.join(chapter.entities[:5])}\n"
            
            if chapter.themes:
                enhanced_chunk += f"Themes: {', '.join(chapter.themes)}\n"
            
            enhanced_chunk += f"\n{chapter.content}"
            
            chunks.append(enhanced_chunk)
        
        return chunks
    
    def get_section_chunks(self, section_index: SectionIndex) -> List[str]:
        """
        Get section-level text chunks ready for vector database indexing.
        
        Returns:
            List of enhanced section chunks optimized for detailed search
        """
        chunks = []
        
        for section in section_index.sections:
            # Enhance section with metadata for better retrieval
            enhanced_chunk = f"Chapter {section.chapter_number} - Section {section.section_index}\n"
            enhanced_chunk += f"[{section.semantic_type.upper()}]\n"
            
            if section.entities:
                enhanced_chunk += f"Entities: {', '.join(section.entities)}\n"
            
            if section.themes:
                enhanced_chunk += f"Themes: {', '.join(section.themes)}\n"
            
            enhanced_chunk += f"\n{section.content}"
            
            chunks.append(enhanced_chunk)
        
        return chunks
    
    def save_indexes(self, chapter_index: ChapterIndex, section_index: SectionIndex, 
                    chapter_filepath: str = None, section_filepath: str = None):
        """Save both chapter and section indexes to JSON files with configuration metadata."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate filepaths with timestamps
        if chapter_filepath is None:
            chapter_filepath = f"./chapter_index_{timestamp}.json"
        else:
            base_name = os.path.splitext(chapter_filepath)[0]
            extension = os.path.splitext(chapter_filepath)[1] or '.json'
            chapter_filepath = f"{base_name}_{timestamp}{extension}"
            
        if section_filepath is None:
            section_filepath = f"./section_index_{timestamp}.json"
        else:
            base_name = os.path.splitext(section_filepath)[0]
            extension = os.path.splitext(section_filepath)[1] or '.json'
            section_filepath = f"{base_name}_{timestamp}{extension}"
        
        # Convert Chapter Index to serializable format
        chapter_data = {
            'chapters': [
                {
                    'chapter_id': ch.chapter_id,
                    'content': ch.content,
                    'chapter_number': ch.chapter_number,
                    'chapter_title': ch.chapter_title,
                    'start_page': ch.start_page,
                    'end_page': ch.end_page,
                    'token_count': ch.token_count,
                    'word_count': ch.word_count,
                    'summary': ch.summary,
                    'entities': ch.entities,
                    'themes': ch.themes,
                    'section_count': len(ch.chapter_sections)
                }
                for ch in chapter_index.chapters
            ],
            'total_chapters': chapter_index.total_chapters,
            'total_tokens': chapter_index.total_tokens,
            'entities': chapter_index.entities,
            'themes': chapter_index.themes,
            'metadata': chapter_index.metadata
        }
        
        # Convert Section Index to serializable format
        section_data = {
            'sections': [
                {
                    'section_id': sec.section_id,
                    'content': sec.content,
                    'chapter_number': sec.chapter_number,
                    'section_index': sec.section_index,
                    'token_count': sec.token_count,
                    'word_count': sec.word_count,
                    'semantic_type': sec.semantic_type,
                    'entities': sec.entities,
                    'themes': sec.themes,
                    'parent_chapter_id': sec.parent_chapter_id
                }
                for sec in section_index.sections
            ],
            'total_sections': section_index.total_sections,
            'total_tokens': section_index.total_tokens,
            'chapters_covered': section_index.chapters_covered,
            'entities': section_index.entities,
            'themes': section_index.themes,
            'metadata': section_index.metadata
        }
        
        # Save both indexes
        with open(chapter_filepath, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
            
        with open(section_filepath, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
        
        if self.cfg.verbose:
            print(f"Chapter index saved to {chapter_filepath}")
            print(f"Section index saved to {section_filepath}")
            print(f"Configuration used: {self.cfg.model_name} with {self.cfg.min_section_tokens} min tokens per section")
        
        return chapter_filepath, section_filepath



# Factory function
def create_chapter_chunker(config: ChapterChunkerConfig = None) -> ChapterChunker:
    """
    Factory function to create a chapter chunker for hierarchical indexes.
    
    Args:
        config: Optional ChapterChunkerConfig. If None, uses default configuration.
        
    Returns:
        Configured ChapterChunker instance ready for processing
    """
    if config is None:
        config = ChapterChunkerConfig()
    
    return ChapterChunker(config)