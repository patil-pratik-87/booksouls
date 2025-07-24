#!/usr/bin/env python3
"""
Test script for DialogueChunker - Tests character-focused dialogue extraction
"""

import os
import sys
from pathlib import Path

# Add parent directory and src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from src.chunkers.dialogue_chunker import create_dialogue_chunker, create_openai_dialogue_chunker
from src.pdf_chapter_extractor import create_chapter_extractor
from src.chunkers.config.config import PDFExtractorConfig
from dotenv import load_dotenv, find_dotenv

def test_dialogue_chunker_single_chapter():
    """Test DialogueChunker with just the first chapter"""
    
    # Configuration
    PDF_PATH = "./data/sample_books/j-r-r-tolkien-lord-of-the-rings-01-the-fellowship-of-the-ring-retail-pdf.pdf"
    
    print("Testing DialogueChunker with Character-Focused Extraction")
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
        
        # Step 2: Test with just the first chapter (rich in dialogue)
        first_chapter = chapters[3]  # Chapter 1 has good dialogue content
        print(f"\nTesting with: Chapter {first_chapter.chapter_number} - {first_chapter.chapter_title}")
        print(f"Chapter stats: {first_chapter.word_count:,} words, {first_chapter.token_count:,} tokens")
        print(f"Section chunks: {len(first_chapter.chunks)}")
        
        # Step 3: Create DialogueChunker and process
        print(f"\nStep 2: Creating dialogue index...")
        dialogue_chunker = create_openai_dialogue_chunker()  # Use OpenAI GPT-4o-mini
        
        # Process only the first chapter
        dialogue_index = dialogue_chunker.create_dialogue_index([first_chapter])
        
        # Step 4: Display results
        print(f"\nStep 3: Processing Results")
        print("=" * 40)
        
        # Dialogue Index Results
        print(f"DIALOGUE INDEX:")
        print(f"   Scenes: {dialogue_index.total_scenes}")
        print(f"   Dialogues: {dialogue_index.total_dialogues}")
        print(f"   Characters: {len(dialogue_index.characters)}")
        print(f"   Character list: {dialogue_index.characters}")
        
        # Show first 3 scenes as examples
        print(f"\nSCENE EXAMPLES:")
        for i, scene in enumerate(dialogue_index.scenes[:3]):
            print(f"\n   Scene {i+1}: {scene.scene_id}")
            print(f"     Setting: {scene.setting}")
            print(f"     Participants: {scene.participants}")
            print(f"     Dialogues: {len(scene.dialogues)}")
            
            # Show first dialogue in scene
            if scene.dialogues:
                dialogue = scene.dialogues[0]
                print(f"     Sample dialogue:")
                print(f"       {dialogue.character}: \"{dialogue.dialogue[:50]}...\"")
                print(f"       Emotion: {dialogue.emotion}")
                print(f"       To: {dialogue.addressee}")
        
        # Character-focused analysis
        print(f"\nCHARACTER ANALYSIS:")
        for character, dialogues in dialogue_index.by_character.items():
            print(f"   {character}: {len(dialogues)} dialogues")
            
            # Show character's first dialogue
            if dialogues:
                first_dialogue = dialogues[0]
                print(f"     Sample: \"{first_dialogue.dialogue[:50]}...\"")
                print(f"     Common emotions: {[d.emotion for d in dialogues[:3]]}")
        
        # Step 5: Test chunk generation for embedding
        print(f"\nStep 4: Generating embedding-ready chunks...")
        
        dialogue_chunks = dialogue_chunker.get_dialogue_chunks(dialogue_index)
        character_chunks = dialogue_chunker.get_character_chunks(dialogue_index)
        
        print(f"   Scene-based chunks: {len(dialogue_chunks)}")
        print(f"   Character-specific chunks: {sum(len(chunks) for chunks in character_chunks.values())}")
        
        # Show sample chunks
        if dialogue_chunks:
            print(f"\nSample Scene Chunk:")
            print(f"{dialogue_chunks[0][:300]}...")
        
        if character_chunks:
            first_character = list(character_chunks.keys())[0]
            print(f"\nSample Character Chunk ({first_character}):")
            print(f"{character_chunks[first_character][0][:300]}...")
        
        # Step 6: Save dialogue index
        print(f"\nStep 5: Saving dialogue index...")
        dialogue_file = dialogue_chunker.save_dialogue_index(
            dialogue_index,
            "./data/outputs/dialogue_index.json"
        )
        
        # Final summary
        print(f"\nTEST COMPLETED SUCCESSFULLY!")
        print("=" * 40)
        print(f"Processed: {first_chapter.chapter_title}")
        print(f"Created: {dialogue_index.total_scenes} scenes with {dialogue_index.total_dialogues} dialogues")
        print(f"Found: {len(dialogue_index.characters)} speaking characters")
        print(f"Characters: {', '.join(dialogue_index.characters[:5])}{'...' if len(dialogue_index.characters) > 5 else ''}")
        print(f"Saved: {dialogue_file}")
        print(f"\nDialogueChunker is working correctly!")
        
        # Extra analysis
        if dialogue_index.total_dialogues > 0:
            print(f"\nDETAILED ANALYSIS:")
            print(f"   Avg dialogues per scene: {dialogue_index.metadata.get('avg_dialogues_per_scene', 0):.1f}")
            print(f"   Most active character: {max(dialogue_index.by_character.keys(), key=lambda k: len(dialogue_index.by_character[k]))}")
            
            # Emotional analysis
            all_emotions = []
            for scene in dialogue_index.scenes:
                for dialogue in scene.dialogues:
                    all_emotions.append(dialogue.emotion)
            
            from collections import Counter
            emotion_counts = Counter(all_emotions)
            print(f"   Common emotions: {dict(emotion_counts.most_common(3))}")
        
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


def create_test_output_dir():
    """Create test output directory if it doesn't exist"""
    os.makedirs("./data/outputs", exist_ok=True)


if __name__ == "__main__":
    print("DialogueChunker Character-Focused Test")
    print("This will test character dialogue extraction with GPT-4o-mini analysis")
    print()
    
    # Create output directory
    # create_test_output_dir()
    
    # Run the test
    test_dialogue_chunker_single_chapter()