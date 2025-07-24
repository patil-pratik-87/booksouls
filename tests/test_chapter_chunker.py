#!/usr/bin/env python3
"""
Test script for ChapterChunker - Tests hierarchical indexing with first chapter only
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.chunkers.config.config import PDFExtractorConfig
from src.chunkers.chapter_chunker import create_chapter_chunker
from src.pdf_chapter_extractor import create_chapter_extractor


def test_chapter_chunker_single_chapter():
    """Test ChapterChunker with just the first chapter"""
    
    # Configuration
    PDF_PATH = "./data/sample_books/j-r-r-tolkien-lord-of-the-rings-01-the-fellowship-of-the-ring-retail-pdf.pdf"
    
    print("=" * 60)
    
    # Check if PDF exists
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found: {PDF_PATH}")
        print("Please place your test PDF in the data/sample_books/ directory")
        return
    
    load_dotenv(find_dotenv())
    
    try:
        # Step 1: Extract chapters from PDF
        print("\nStep 1: Extracting chapters from PDF...")
        config = PDFExtractorConfig()
        extractor = create_chapter_extractor(PDF_PATH, config)
        chapters = extractor.extract_chapters_from_pdf()
        
        if not chapters:
            print("ERROR: No chapters found in PDF")
            return
        
        print(f"Found {len(chapters)} chapters")
        
        # Step 2: Test with just the first chapter
        first_chapter = chapters[3]
        print(f"\nTesting with: Chapter {first_chapter.chapter_number} - {first_chapter.chapter_title}")
        print(f"Chapter stats: {first_chapter.word_count:,} words, {first_chapter.token_count:,} tokens")
        
        # Step 3: Create ChapterChunker and process
        print(f"\nStep 2: Creating hierarchical indexes...")
        chunker = create_chapter_chunker()  # No parameters needed - uses existing chunks
        
        # Process only the first chapter
        chapter_index, section_index = chunker.create_hierarchical_indexes([first_chapter])
        
        # Step 4: Display results
        print(f"\nStep 3: Processing Results")
        print("=" * 40)
        
        # Chapter Index Results
        chapter = chapter_index.chapters[0]
        print(f"CHAPTER INDEX:")
        print(f"   Chapter: {chapter.chapter_number} - {chapter.chapter_title}")
        print(f"   Summary: {chapter.summary[:100]}...")
        print(f"   Entities: {chapter.entities[:5]}")  # First 5 entities
        print(f"   Themes: {chapter.themes}")
        print(f"   Sections: {len(chapter.chapter_sections)}")
        
        # Section Index Results  
        print(f"\nSECTION INDEX:")
        print(f"   Total sections: {section_index.total_sections}")
        print(f"   Total tokens: {section_index.total_tokens:,}")
        
        # Show first 3 sections as examples
        for i, section in enumerate(section_index.sections[:3]):
            print(f"\n   Section {i+1}: {section.section_id}")
            print(f"     Type: {section.semantic_type}")
            print(f"     Tokens: {section.token_count}")
            print(f"     Entities: {section.entities[:3]}")  # First 3 entities
            print(f"     Themes: {section.themes}")
            print(f"     Preview: {section.content[:100]}...")
        
        # Step 5: Test chunk generation for embedding
        print(f"\nStep 4: Generating embedding-ready chunks...")
        
        chapter_chunks = chunker.get_chapter_chunks(chapter_index)
        section_chunks = chunker.get_section_chunks(section_index)
        
        print(f"   Chapter chunks: {len(chapter_chunks)}")
        print(f"   Section chunks: {len(section_chunks)}")
        
        # Show sample enhanced chunks
        print(f"\nSample Chapter Chunk:")
        print(f"{chapter_chunks[0][:300]}...")
        
        print(f"\nSample Section Chunk:")
        print(f"{section_chunks[0][:300]}...")
        
        # Step 6: Save indexes
        print(f"\nStep 5: Saving indexes...")
        chapter_file, section_file = chunker.save_indexes(
            chapter_index, section_index,
            "./data/outputs/chapter_index.json",
            "./data/outputs/section_index.json"
        )
        
        # Final summary
        print(f"\nTEST COMPLETED SUCCESSFULLY!")
        print("=" * 40)
        print(f"Processed: {chapter.chapter_title}")
        print(f"🔧 Created: {section_index.total_sections} sections from 1 chapter")
        print(f"Found: {len(chapter.entities)} entities, {len(chapter.themes)} themes")
        print(f"Saved: {chapter_file}")
        print(f"Saved: {section_file}")
        print(f"\nChapterChunker is working correctly!")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            extractor.close()
        except:
            pass



if __name__ == "__main__":
    print("🧪 ChapterChunker Single Chapter Test")
    print("This will test the hierarchical indexing with GPT-4o-mini analysis")
    print()
    
    # Create output directory
    
    # Run the test
    test_chapter_chunker_single_chapter()

