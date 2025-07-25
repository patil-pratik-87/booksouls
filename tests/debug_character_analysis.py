#!/usr/bin/env python3
"""
Debug script to test character analysis functionality
"""

import json
import os
from src.chunkers.dialogue_chunker import DialogueChunker, DialogueIndex
from dotenv import load_dotenv, find_dotenv

def test_character_analysis():
    # Load existing dialogue index
    load_dotenv(find_dotenv())
    index_path = "data/outputs/dialogue_index_20250725_003133.json"
    print(f"Loading dialogue index from: {index_path}")
    
    try:
        dialogue_index = DialogueChunker.load_dialogue_index(index_path)
        print(f"Loaded dialogue index with {len(dialogue_index.characters)} characters")
        print(f"Characters: {dialogue_index.characters[:5]}...")
        print(f"Character profiles: {len(dialogue_index.character_profiles)} profiles")
        
        # Check scenes
        if dialogue_index.scenes:
            first_scene = dialogue_index.scenes[0]
            print(f"\nFirst scene analysis:")
            print(f"  Scene ID: {first_scene.scene_id}")
            print(f"  Participants: {first_scene.participants}")
            print(f"  Dialogues: {len(first_scene.dialogues)}")
            
            # Check character dialogue count
            char_counts = {}
            for scene in dialogue_index.by_chapter.get(1, []):
                for dialogue in scene.dialogues:
                    char = dialogue.character
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            print(f"\nChapter 1 character dialogue counts:")
            sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)
            for char, count in sorted_chars[:5]:
                print(f"  {char}: {count} dialogues")
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        print(f"\nOpenAI API Key: {'Set' if api_key else 'NOT SET'}")
        
        # Show configuration used
        print(f"\nConfiguration used:")
        print(f"  Model: {dialogue_index.metadata['config_used']['model_name']}")
        print(f"  Top characters per chapter: {dialogue_index.metadata['config_used']['top_characters_per_chapter']}")
        print(f"  Max sample dialogues: {dialogue_index.metadata['config_used']['max_sample_dialogues']}")
        
    except Exception as e:
        print(f"Error loading dialogue index: {e}")
        import traceback
        traceback.print_exc()

def test_character_selection():
    """Test the character selection logic directly"""
    print("\n" + "="*50)
    print("Testing character selection logic...")
    
    try:
        # Load the dialogue index
        index_path = "data/outputs/dialogue_index_20250725_003133.json"
        dialogue_index = DialogueChunker.load_dialogue_index(index_path)
        
        # Get chapter 1 scenes
        chapter_1_scenes = dialogue_index.by_chapter.get(1, [])
        print(f"Chapter 1 has {len(chapter_1_scenes)} scenes")
        
        # Manually test character selection
        from src.chunkers.config.config import DialogueChunkerConfig
        
        config = DialogueChunkerConfig(verbose=True)
        chunker = DialogueChunker(config)
        
        # Test character selection
        selected = chunker._select_characters_for_analysis(chapter_1_scenes)
        print(f"Selected characters: {selected}")
        
        if selected:
            print(f"Would analyze {len(selected)} characters")
            
            # Test character data preparation
            character_data = chunker._prepare_character_data_for_analysis(selected, chapter_1_scenes)
            print(f"Character data prepared for: {list(character_data.keys())}")
            
            for char, data in character_data.items():
                print(f"  {char}: {len(data['dialogue_entries'])} dialogue entries")
            
            # Test the character analysis prompt creation
            prompt = chunker._create_character_analysis_prompt(character_data, 1)
            print(f"\nCharacter analysis prompt length: {len(prompt)} characters")
            print(f"Prompt preview: {prompt[:200]}...")
            
            # Test LLM call directly (this will reveal the real issue)
            print(f"\nTesting LLM call...")
            response = chunker._generate_openai_response(prompt)
            if response:
                print(f"LLM Response received: {len(response)} characters")
                print(f"Response preview: {response[:200]}...")
            else:
                print("LLM Response: None (this is the problem!)")
        
    except Exception as e:
        print(f"Error in character selection test: {e}")
        import traceback
        traceback.print_exc()

def add_character_profiles_to_existing_index():
    """Add character profiles to existing dialogue index without regenerating everything."""
    print("\n" + "="*50)
    print("Adding character profiles to existing dialogue index...")
    
    try:
        # Load existing dialogue index
        load_dotenv(find_dotenv())
        index_path = "data/outputs/dialogue_index_20250725_003133.json"
        dialogue_index = DialogueChunker.load_dialogue_index(index_path)
        
        print(f"Loaded dialogue index with {len(dialogue_index.characters)} characters")
        print(f"Current character profiles: {len(dialogue_index.character_profiles)}")
        
        # Create chunker for character analysis
        from src.chunkers.config.config import DialogueChunkerConfig
        config = DialogueChunkerConfig(verbose=True)
        chunker = DialogueChunker(config)
        
        # Process each chapter and add character profiles
        character_profiles = {}
        
        for chapter_num, chapter_scenes in dialogue_index.by_chapter.items():
            print(f"\nAnalyzing characters in Chapter {chapter_num}...")
            
            # Select top characters for this chapter
            selected_characters = chunker._select_characters_for_analysis(chapter_scenes)
            
            if selected_characters:
                try:
                    # Analyze selected characters
                    profiles = chunker._analyze_chapter_characters(
                        selected_characters, chapter_scenes, chapter_num
                    )
                    
                    # Store profiles by character
                    for profile in profiles:
                        if profile.name not in character_profiles:
                            character_profiles[profile.name] = []
                        character_profiles[profile.name].append(profile)
                        print(f"  Added profile for {profile.name}: {profile.personality_traits}")
                        
                except Exception as e:
                    print(f"  Warning: Failed to analyze characters in Chapter {chapter_num}: {str(e)}")
                    continue
        
        # Update the dialogue index with new character profiles
        dialogue_index.character_profiles = character_profiles
        
        # Update metadata
        total_profiles = sum(len(profiles) for profiles in character_profiles.values())
        dialogue_index.metadata['characters_analyzed'] = len(character_profiles)
        dialogue_index.metadata['total_character_profiles'] = total_profiles
        dialogue_index.metadata['profile_analysis_added'] = True
        
        print(f"\nCharacter profile analysis complete!")
        print(f"  Characters analyzed: {len(character_profiles)}")
        print(f"  Total profiles created: {total_profiles}")
        
        # Save updated dialogue index
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/outputs/dialogue_index_with_profiles_{timestamp}.json"
        
        # Use the existing save method
        temp_chunker = DialogueChunker(config)
        saved_path = temp_chunker.save_dialogue_index(dialogue_index, output_path)
        
        print(f"\nUpdated dialogue index saved to: {saved_path}")
        print("You can now use this file in the UI to see character profiles!")
        
        return dialogue_index, saved_path
        
    except Exception as e:
        print(f"Error adding character profiles: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def quick_add_profiles():
    """Quick function to just add profiles and save - no debugging output."""
    print("Adding character profiles to existing dialogue index...")
    
    try:
        load_dotenv(find_dotenv())
        index_path = "data/outputs/dialogue_index_20250725_003133.json"
        dialogue_index = DialogueChunker.load_dialogue_index(index_path)
        
        from src.chunkers.config.config import DialogueChunkerConfig
        config = DialogueChunkerConfig(verbose=False)  # Quiet mode
        chunker = DialogueChunker(config)
        
        character_profiles = {}
        
        for chapter_num, chapter_scenes in dialogue_index.by_chapter.items():
            selected_characters = chunker._select_characters_for_analysis(chapter_scenes)
            
            if selected_characters:
                try:
                    profiles = chunker._analyze_chapter_characters(
                        selected_characters, chapter_scenes, chapter_num
                    )
                    
                    for profile in profiles:
                        if profile.name not in character_profiles:
                            character_profiles[profile.name] = []
                        character_profiles[profile.name].append(profile)
                        
                except Exception:
                    continue
        
        dialogue_index.character_profiles = character_profiles
        
        # Update metadata
        total_profiles = sum(len(profiles) for profiles in character_profiles.values())
        dialogue_index.metadata['characters_analyzed'] = len(character_profiles)
        dialogue_index.metadata['total_character_profiles'] = total_profiles
        
        # Save with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/outputs/dialogue_index_with_profiles_{timestamp}.json"
        
        temp_chunker = DialogueChunker(DialogueChunkerConfig())
        saved_path = temp_chunker.save_dialogue_index(dialogue_index, output_path)
        
        print(f"✅ Character profiles added! New file: {saved_path}")
        print(f"📊 {len(character_profiles)} characters analyzed, {total_profiles} total profiles")
        
        return saved_path
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--add-profiles":
        # Quick mode: just add profiles
        quick_add_profiles()
    elif len(sys.argv) > 1 and sys.argv[1] == "--add-profiles-verbose":
        # Verbose mode: add profiles with debug output
        add_character_profiles_to_existing_index()
    else:
        # Default: run tests
        test_character_analysis()
        test_character_selection()