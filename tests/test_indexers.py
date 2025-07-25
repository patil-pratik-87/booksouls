"""
Simple test script for BookSouls Dual Vector Indexer

Loads real data from ./data/outputs/ and sets up vector stores for querying.
"""

import os
import sys
import json
import glob
import dotenv

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.indexers.config import get_default_config, get_openai_config
from src.indexers.dual_vector_indexer import create_dual_indexer
from src.chunkers.chapter_chunker import SectionChunk, SectionIndex
from src.chunkers.dialogue_chunker import DialogueIndex, ConversationScene, CharacterDialogue
from config import load_test_config


def load_real_data(config=None):
    """Load the latest section and dialogue indexes from data/outputs."""
    if config is None:
        config = load_test_config()
    
    base_dir = os.path.join(os.path.dirname(__file__), config.data_base_dir)
    
    # Find latest files
    section_files = glob.glob(os.path.join(base_dir, 'section_index_*.json'))
    dialogue_files = glob.glob(os.path.join(base_dir, 'dialogue_index_*.json'))
    
    if not section_files or not dialogue_files:
        print("❌ No index files found in data/outputs/")
        return None, None
    
    latest_section = max(section_files, key=os.path.getmtime)
    latest_dialogue = max(dialogue_files, key=os.path.getmtime)
    
    print(f"📖 Loading: {os.path.basename(latest_section)}")
    print(f"💬 Loading: {os.path.basename(latest_dialogue)}")
    
    # Load section index
    with open(latest_section, 'r', encoding='utf-8') as f:
        section_data = json.load(f)
    
    sections = [
        SectionChunk(
            section_id=s['section_id'],
            content=s['content'],
            chapter_number=s['chapter_number'],
            section_index=s['section_index'],
            token_count=s['token_count'],
            word_count=s['word_count'],
            semantic_type=s['semantic_type'],
            entities=s['entities'],
            themes=s['themes'],
            parent_chapter_id=s['parent_chapter_id']
        ) for s in section_data['sections']
    ]
    
    section_index = SectionIndex(
        sections=sections,
        total_sections=section_data['total_sections'],
        total_tokens=section_data['total_tokens'],
        chapters_covered=section_data['chapters_covered'],
        entities=section_data['entities'],
        themes=section_data['themes'],
        metadata=section_data['metadata']
    )
    
    # Load dialogue index
    with open(latest_dialogue, 'r', encoding='utf-8') as f:
        dialogue_data = json.load(f)
    
    scenes = []
    for scene_data in dialogue_data['scenes']:
        dialogues = [
            CharacterDialogue(
                character=d['character'],
                dialogue=d['dialogue'],
                addressee=d['addressee'],
                context=d['context'],
                emotion=d['emotion'],
                actions=d['actions'],
                scene_id=d['scene_id'],
                chapter_number=d['chapter_number'],
                section_id=d['section_id']
            ) for d in scene_data['dialogues']
        ]
        
        scene = ConversationScene(
            scene_id=scene_data['scene_id'],
            participants=scene_data['participants'],
            dialogues=dialogues,
            setting=scene_data['setting'],
            context=scene_data['context'],
            chapter_number=scene_data['chapter_number']
        )
        scenes.append(scene)
    
    by_character = {}
    for char, char_dialogues in dialogue_data['by_character'].items():
        by_character[char] = [
            CharacterDialogue(
                character=d['character'],
                dialogue=d['dialogue'],
                addressee=d['addressee'],
                context=d['context'],
                emotion=d['emotion'],
                actions=d['actions'],
                scene_id=d['scene_id'],
                chapter_number=d['chapter_number'],
                section_id=d['section_id']
            ) for d in char_dialogues
        ]
    
    # Load character profiles if they exist
    character_profiles = {}
    if 'character_profiles' in dialogue_data:
        from src.chunkers.dialogue_chunker import CharacterProfile
        for character, profiles_data in dialogue_data['character_profiles'].items():
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

    dialogue_index = DialogueIndex(
        scenes=scenes,
        by_character=by_character,
        by_chapter={},
        character_profiles=character_profiles,
        total_dialogues=dialogue_data['total_dialogues'],
        total_scenes=dialogue_data['total_scenes'],
        characters=dialogue_data['characters'],
        chapters_covered=dialogue_data['chapters_covered'],
        metadata=dialogue_data['metadata']
    )
    
    print(f"✅ Loaded {len(sections)} sections and {dialogue_data['total_dialogues']} dialogues")
    return section_index, dialogue_index


def setup_indexer(test_config=None, api_key=None):
    """Setup dual vector indexer."""
    if test_config is None:
        test_config = load_test_config()
    
    use_openai = test_config.use_openai
    
    if use_openai:
        # Debug: Check environment variable
        dotenv.load_dotenv(dotenv.find_dotenv())

        env_key = os.getenv('OPENAI_API_KEY')
        config_key = test_config.openai_api_key
        
        if test_config.verbose_output:
            print(f"🔍 Environment API key found: {'Yes' if env_key else 'No'}")
            print(f"🔍 Config API key found: {'Yes' if config_key else 'No'}")
            print(f"🔍 API key parameter: {'Yes' if api_key else 'No'}")
        
        # Use parameter > config > environment priority
        final_key = api_key or config_key or env_key
            
        if not final_key:
            print("❌ No API key found in parameter, config, or environment")
            return None
            
        config = get_openai_config(final_key)
        config.base_persist_dir = test_config.base_persist_dir
        if test_config.verbose_output:
            print("🔧 Using OpenAI embeddings")
    else:
        config = get_default_config()
        config.base_persist_dir = test_config.base_persist_dir
        if test_config.verbose_output:
            print("🔧 Using default ChromaDB embeddings")
    
    return create_dual_indexer(config)


def index_data(indexer, test_config=None):
    """Load and index the data."""
    if test_config is None:
        test_config = load_test_config()
    
    # Check if collections already contain data
    stats = indexer.get_stats()
    if stats['total_documents'] > 0 and test_config.skip_indexing_if_exists:
        if test_config.verbose_output:
            print(f"Collections already indexed with {stats['total_documents']} documents")
            print(f"Narrative: {stats['narrative_store']['document_count']} docs")
            print(f"Dialogue: {stats['dialogue_store']['document_count']} docs")
            print("Skipping indexing...")
        return indexer
    
    section_index, dialogue_index = load_real_data(test_config)
    
    if not section_index or not dialogue_index:
        return None
    
    if test_config.verbose_output:
        print("\n📊 Indexing data...")
    
    narrative_result = indexer.index_narrative_chunks(section_index)
    dialogue_result = indexer.index_dialogue_chunks(dialogue_index)
    
    if test_config.verbose_output:
        print(f"✅ Indexed {narrative_result['total_chunks']} narrative chunks")
        print(f"✅ Indexed {dialogue_result['total_chunks']} dialogue chunks")
    
    return indexer


def interactive_query(indexer, test_config=None):
    """Interactive query interface."""
    if test_config is None:
        test_config = load_test_config()
    
    print("\n🔍 Interactive Query Mode")
    print("Commands:")
    print("  n <query>     - Search narrative")
    print("  d <query>     - Search dialogue") 
    print("  c <character> - Get character dialogues")
    print("  ch <number>   - Get chapter content")
    print("  t <theme>     - Search by theme")
    print("  p <query>     - Search character profiles")
    print("  traits <trait> - Find characters by trait")
    print("  similar <char> - Find similar characters")
    print("  stats         - Show statistics")
    print("  help          - Show commands")
    print("  quit          - Exit")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            elif user_input.lower() in ['help', 'h']:
                print("Commands:")
                print("  n <query>     - Search narrative")
                print("  d <query>     - Search dialogue") 
                print("  c <character> - Get character dialogues")
                print("  ch <number>   - Get chapter content")
                print("  t <theme>     - Search by theme")
                print("  p <query>     - Search character profiles")
                print("  traits <trait> - Find characters by trait")
                print("  similar <char> - Find similar characters")
                print("  stats         - Show statistics")
                
            elif user_input.lower() == 'stats':
                stats = indexer.get_stats()
                print(f"📈 Statistics:")
                print(f"   Narrative docs: {stats['narrative_store']['document_count']}")
                print(f"   Dialogue docs: {stats['dialogue_store']['document_count']}")
                print(f"   Total: {stats['total_documents']}")
                
            elif user_input.startswith('n '):
                query = user_input[2:].strip()
                if query:
                    results = indexer.query_narrative(query, n_results=test_config.default_n_results)
                    print_results(results, f"Narrative: '{query}'", test_config)
                    
            elif user_input.startswith('d '):
                query = user_input[2:].strip()
                if query:
                    results = indexer.query_dialogue(query, n_results=test_config.default_n_results)
                    print_results(results, f"Dialogue: '{query}'", test_config)
                    
            elif user_input.startswith('c '):
                character = user_input[2:].strip()
                if character:
                    results = indexer.get_character_dialogues(character, limit=test_config.default_n_results)
                    print_results(results, f"Character: {character}", test_config)
                    
            elif user_input.startswith('ch '):
                try:
                    chapter_num = int(user_input[3:].strip())
                    results = indexer.get_chapter_content(chapter_num)
                    print_results(results, f"Chapter {chapter_num}", test_config)
                except ValueError:
                    print("❌ Invalid chapter number")
                    
            elif user_input.startswith('t '):
                theme = user_input[2:].strip()
                if theme:
                    results = indexer.get_thematic_content(theme, n_results=test_config.default_n_results)
                    print_results(results, f"Theme: {theme}", test_config)
                    
            elif user_input.startswith('p '):
                query = user_input[2:].strip()
                if query:
                    results = indexer.query_character_profiles(query, n_results=test_config.default_n_results)
                    print_results(results, f"Character Profiles: '{query}'", test_config)
                    
            elif user_input.startswith('traits '):
                trait = user_input[7:].strip()
                if trait:
                    results = indexer.get_character_by_traits([trait], n_results=test_config.default_n_results)
                    print_results(results, f"Characters with trait: {trait}", test_config)
                    
            elif user_input.startswith('similar '):
                character = user_input[8:].strip()
                if character:
                    results = indexer.find_similar_characters(character, n_results=test_config.default_n_results)
                    print_results(results, f"Characters similar to: {character}", test_config)
                    
            else:
                print("❌ Unknown command. Type 'help' for commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n👋 Goodbye!")


def print_results(results, title, test_config=None):
    """Print query results nicely."""
    if test_config is None:
        test_config = load_test_config()
    
    if 'results' not in results:
        print("❌ No results")
        return
        
    query_results = results['results']
    ids = query_results['ids'][0] if query_results['ids'] else []
    
    print(f"\n=== {title} ===")
    print(f"Found {len(ids)} results:")
    
    max_display = min(len(ids), test_config.max_results_display)
    
    for i, doc_id in enumerate(ids[:max_display]):
        print(f"\n{i+1}. {doc_id}")
        
        # Show content preview
        if 'documents' in query_results and i < len(query_results['documents'][0]):
            content = query_results['documents'][0][i]
            preview = content[:test_config.content_preview_length].replace('\n', ' ')
            print(f"   📄 {preview}...")
            
        # Show metadata
        if 'metadatas' in query_results and i < len(query_results['metadatas'][0]):
            metadata = query_results['metadatas'][0][i]
            if 'character' in metadata:
                print(f"   👤 Character: {metadata['character']}")
            if 'semantic_type' in metadata:
                print(f"   📝 Type: {metadata['semantic_type']}")
            if 'emotion' in metadata:
                print(f"   😊 Emotion: {metadata['emotion']}")


def main():
    """Setup indexer and start interactive mode."""
    test_config = load_test_config()
    
    if test_config.verbose_output:
        print("🚀 BookSouls Interactive Vector Query")
        print("=" * 40)
    
    # Setup indexer
    indexer = setup_indexer(test_config)
    
    # Load and index data
    indexer = index_data(indexer, test_config)
    if not indexer:
        print("❌ Failed to load data")
        return
    
    # Start interactive mode if configured
    if test_config.interactive_mode:
        interactive_query(indexer, test_config)
    
    return indexer


if __name__ == "__main__":
    main()