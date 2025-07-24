#!/usr/bin/env python3
"""
PDF Chapter Extractor using PyMuPDF - Enhanced for BookSouls Dual-Index Architecture
Extracts chapters and processes them for both Character and Narrative indices.
"""

import fitz  # PyMuPDF
import re
import time
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.chunkers.config.config import PDFExtractorConfig


@dataclass
class ChapterChunk:
    chapter_number: int
    chapter_title: str
    content: str
    chunks: List[str]  # Token chunks for processing
    start_page: int
    end_page: int
    word_count: int
    token_count: int  # Total tokens in chapter content


class PDFChapterExtractor:
    def __init__(self, pdf_path: str, cfg: PDFExtractorConfig = PDFExtractorConfig()):
        """
        Initialize the PDF chapter extractor with chunking capabilities.
        
        Args:
            pdf_path: Path to the PDF file
            cfg: PDFExtractorConfig with chunk_size, chunk_overlap, and other settings
        """
        self.cfg = cfg
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.doc = fitz.open(str(self.pdf_path))
        
        # Initialize text splitter for token-based chunking using config
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.cfg.chunk_size,
            chunk_overlap=self.cfg.chunk_overlap,
            length_function=self._count_tokens,
            separators=self.cfg.text_separators
        )
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
    
    def extract_chapters_from_pdf(self) -> List[ChapterChunk]:
        """
        Extract chapter-level chunks from PDF using fitz.
        Enhanced version from ChunkAccuracyTester.py for dual-index architecture.
        """
        start_time = time.time()
        
        try:
            chapters = []
            
            # Chapter detection patterns from config
            chapter_patterns = self.cfg.chapter_patterns
            
            current_chapter = None
            chapter_content = []
            
            if self.cfg.verbose:
                print(f"📖 Processing PDF: {self.pdf_path}")
                print(f"📄 Total pages: {self.doc.page_count}")
                print(f"🔍 Using {len(chapter_patterns)} chapter detection patterns")
            
            for page_num in range(self.doc.page_count):
                page = self.doc[page_num]
                text = page.get_text()
                
                # Skip empty pages if configured
                if self.cfg.skip_empty_pages and len(text.strip()) < self.cfg.min_page_chars:
                    continue
                
                # Check for chapter start
                chapter_match = None
                for pattern in chapter_patterns:
                    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                    if match:
                        chapter_match = match
                        break
                
                # If we found a new chapter, save the previous one
                if chapter_match and current_chapter is not None:
                    self._finalize_chapter(current_chapter, chapter_content, chapters, page_num - 1)
                    chapter_content = []
                
                # Start new chapter if found
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                    chapter_title = chapter_match.group(2).strip() if len(chapter_match.groups()) > 1 else f"Chapter {chapter_num}"
                    
                    current_chapter = {
                        'number': chapter_num,
                        'title': chapter_title,
                        'start_page': page_num + 1  # 1-indexed
                    }
                    if self.cfg.verbose:
                        print(f"Found Chapter {chapter_num}: {chapter_title} (page {page_num + 1})")
                
                # Add content to current chapter
                if current_chapter is not None:
                    chapter_content.append(text)
            
            # Finalize the last chapter
            if current_chapter is not None:
                self._finalize_chapter(current_chapter, chapter_content, chapters, self.doc.page_count)
            
            processing_time = time.time() - start_time
            if self.cfg.verbose:
                print(f"✅ Extracted {len(chapters)} chapters in {processing_time:.2f}s")
            
            return chapters
            
        except Exception as e:
            if self.cfg.verbose:
                print(f"❌ Error processing PDF: {str(e)}")
            return []
    
    def _finalize_chapter(self, chapter_info: Dict, content_pages: List[str], 
                         chapters: List[ChapterChunk], end_page: int):
        """Finalize a chapter and add it to the chapters list."""
        full_content = '\n'.join(content_pages)
        word_count = len(full_content.split())
        token_count = self._count_tokens(full_content)
        
        # Use RecursiveTextSplitter to create token chunks
        chunks = self.text_splitter.split_text(full_content)
        
        chapter_chunk = ChapterChunk(
            chapter_number=chapter_info['number'],
            chapter_title=chapter_info['title'],
            content=full_content,
            chunks=chunks,
            start_page=chapter_info['start_page'],
            end_page=end_page,
            word_count=word_count,
            token_count=token_count
        )
        
        chapters.append(chapter_chunk)
        if self.cfg.verbose:
            print(f"   📝 Chapter {chapter_info['number']}: {len(chunks)} chunks, {word_count} words, {token_count} tokens")
    
    def find_chapter_pages(self, chapter_pattern: str) -> Optional[tuple]:
        """
        Find start and end pages for a chapter using pattern matching.
        
        Args:
            chapter_pattern: Regex pattern to match chapter title
            
        Returns:
            Tuple of (start_page, end_page) or None if not found
        """
        toc = self.get_table_of_contents()
        
        # Find the target chapter
        target_chapter_idx = None
        for i, chapter in enumerate(toc):
            if re.search(chapter_pattern, chapter['title'], re.IGNORECASE):
                target_chapter_idx = i
                break
        
        if target_chapter_idx is None:
            if self.cfg.verbose:
                print(f"Chapter matching pattern '{chapter_pattern}' not found")
            return None
        
        start_page = toc[target_chapter_idx]['page']
        
        # Find end page (start of next chapter or end of document)
        if target_chapter_idx + 1 < len(toc):
            end_page = toc[target_chapter_idx + 1]['page'] - 1
        else:
            end_page = self.doc.page_count - 1
        
        return start_page, end_page
    
    def extract_chapter_text_pymupdf(self, start_page: int, end_page: int) -> str:
        """Extract text from specified pages using PyMuPDF"""
        text_content = []
        
        for page_num in range(start_page, end_page + 1):
            if page_num >= self.doc.page_count:
                break
            
            page = self.doc[page_num]
            text = page.get_text()
            text_content.append(text)
        
        return "\n".join(text_content)
    
    
    def list_chapters(self) -> None:
        """Print all available chapters"""
        chapters = self.get_table_of_contents()
        print(f"\nTable of Contents for {self.pdf_path.name}:")
        print("-" * 50)
        
        for chapter in chapters:
            indent = "  " * (chapter['level'] - 1)
            print(f"{indent}Page {chapter['page'] + 1}: {chapter['title']}")
    
    def get_chapter_chunks_for_processing(self, chapters: List[ChapterChunk]) -> List[str]:
        """
        Convert chapter chunks to text chunks ready for further processing.
        Returns a list of text chunks (one per chapter).
        """
        return [chapter.content for chapter in chapters]

    def get_token_chunks_for_processing(self, chapters: List[ChapterChunk]) -> List[str]:
        """
        Convert chapter chunks to token-level chunks for processing.
        Returns a list of token chunks across all chapters.
        """
        all_chunks = []
        for chapter in chapters:
            all_chunks.extend(chapter.chunks)
        return all_chunks
    
    def print_chapter_summary(self, chapters: List[ChapterChunk]):
        """Print a summary of extracted chapters if verbose mode is enabled."""
        if not self.cfg.verbose:
            return
            
        print(f"\n📚 CHAPTER EXTRACTION SUMMARY")
        print("=" * 50)
        
        total_words = sum(ch.word_count for ch in chapters)
        total_tokens = sum(ch.token_count for ch in chapters)
        total_chunks = sum(len(ch.chunks) for ch in chapters)
        
        print(f"📖 Book: {self.pdf_path.name}")
        print(f"📊 Total: {len(chapters)} chapters, {total_words:,} words, {total_tokens:,} tokens, {total_chunks} chunks")
        print(f"⚙️  Config: {self.cfg.chunk_size} tokens/chunk, {self.cfg.chunk_overlap} overlap")
        print()
        
        for chapter in chapters:
            print(f"Chapter {chapter.chapter_number}: {chapter.chapter_title}")
            print(f"  📄 Pages: {chapter.start_page}-{chapter.end_page}")
            print(f"  📝 Chunks: {len(chapter.chunks)} tokens")
            print(f"  📊 Words: {chapter.word_count:,}, Tokens: {chapter.token_count:,}")
            
            # Show first chunk as preview
            if chapter.chunks:
                preview = chapter.chunks[0][:100] + "..." if len(chapter.chunks[0]) > 100 else chapter.chunks[0]
                print(f"  🔍 Preview: {preview}")
            print()

    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()


# Factory function for easy usage
def create_chapter_extractor(pdf_path: str, config: PDFExtractorConfig = None) -> PDFChapterExtractor:
    """
    Factory function to create a PDF chapter extractor.
    
    Args:
        pdf_path: Path to the PDF file
        config: Optional PDFExtractorConfig. If None, uses default configuration.
        
    Returns:
        Configured PDFChapterExtractor instance ready for processing
    """
    if config is None:
        config = PDFExtractorConfig()
    return PDFChapterExtractor(pdf_path, config)


def main():
    """
    Main function to demonstrate PDF chapter extraction.
    
    Replace 'your_book.pdf' with the actual path to your PDF file.
    """
    
    # Example usage - replace with your PDF path
    pdf_path = input("Enter the path to your PDF file: ").strip()
    
    if not pdf_path:
        print("No PDF path provided. Exiting.")
        return
    
    try:
        extractor = PDFChapterExtractor(pdf_path)
        
        # List all chapters first
        extractor.list_chapters()
        
        
        extractor.close()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()