"""
FastAPI Backend for BookSouls Dual Vector Indexer

Provides REST API endpoints to connect the React UI with the dual vector indexer.
Supports narrative and dialogue vector stores with various query types.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import traceback
import dotenv

# BookSouls imports
from ..indexers.dual_vector_indexer import DualVectorIndexer, create_dual_indexer
from ..indexers.config import get_openai_config
from ..chunkers.chapter_chunker import SectionIndex
from ..chunkers.dialogue_chunker import DialogueIndex
from ..agents.character_factory import CharacterFactory

app = FastAPI(
    title="BookSouls Vector Indexer API",
    description="API for dual vector indexing and querying of book content",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global indexer and character factory instances
indexer: Optional[DualVectorIndexer] = None
character_factory: Optional[CharacterFactory] = None

# Request models
class QueryRequest(BaseModel):
    type: str  # 'narrative', 'dialogue', 'character', 'chapter', 'theme'
    query: Optional[str] = None
    character: Optional[str] = None
    chapter_number: Optional[int] = None
    theme: Optional[str] = None
    n_results: Optional[int] = None
    
    # Enhanced dialogue filtering parameters
    dialogue_type: Optional[str] = None  # "scene", "character_dialogue", "character_profile"
    addressee: Optional[str] = None
    emotion: Optional[str] = None
    scene_id: Optional[str] = None
    setting: Optional[str] = None
    participants: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None
    emotional_state: Optional[str] = None

class IndexRequest(BaseModel):
    section_data: Optional[Dict] = None
    dialogue_data: Optional[Dict] = None
    base_persist_dir: Optional[str] = None

class InitializeRequest(BaseModel):
    base_persist_dir: Optional[str] = None
    openai_api_key: Optional[str] = None

# Response models
class StatsResponse(BaseModel):
    narrative_store: Dict[str, Any]
    dialogue_store: Dict[str, Any]
    total_documents: int
    indexing_metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    query: Optional[str] = None
    character_filter: Optional[str] = None
    results: Dict[str, Any]
    store_type: str

# Character chat request models
class CharacterChatRequest(BaseModel):
    character_name: str
    message: str
    conversation_history: Optional[List[Dict]] = None

class CharacterListRequest(BaseModel):
    refresh_cache: Optional[bool] = False

class MultiCharacterChatRequest(BaseModel):
    characters: List[str]
    prompt: str
    max_rounds: Optional[int] = 3

@app.post("/api/indexer/initialize")
async def initialize_indexer(request: InitializeRequest = InitializeRequest()):
    """Initialize the dual vector indexer and character factory."""
    global indexer, character_factory
    
    try:
        # Get configuration - always require OpenAI API key
        dotenv.load_dotenv(dotenv.find_dotenv())
        api_key = request.openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise HTTPException(
                status_code=400, 
                detail="OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass openai_api_key in request."
            )
        
        config = get_openai_config(api_key)
        
        # Set custom persist directory if provided
        if request.base_persist_dir:
            config.base_persist_dir = request.base_persist_dir
        
        # Create indexer
        indexer = create_dual_indexer(config)
        
        # Create character factory
        character_factory = CharacterFactory(indexer)
        
        # Get current stats
        stats = indexer.get_stats()
        
        return {
            "status": "initialized",
            "config": {
                "base_persist_dir": config.base_persist_dir,
                "narrative_collection": config.narrative_collection,
                "dialogue_collection": config.dialogue_collection,
            },
            "stats": stats,
            "character_factory_status": "initialized"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize indexer: {str(e)}")

@app.post("/api/indexer/index")
async def index_data(request: IndexRequest):
    """Index section and/or dialogue data."""
    global indexer
    
    if not indexer:
        raise HTTPException(status_code=400, detail="Indexer not initialized")
    
    try:
        results = {}
        
        # Index section data if provided
        if request.section_data:
            section_index = SectionIndex.from_dict(request.section_data)
            narrative_result = indexer.index_narrative_chunks(section_index)
            results['narrative'] = narrative_result
        
        # Index dialogue data if provided
        if request.dialogue_data:
            dialogue_index = DialogueIndex.from_dict(request.dialogue_data)
            dialogue_result = indexer.index_dialogue_chunks(dialogue_index)
            results['dialogue'] = dialogue_result
        
        if not results:
            raise HTTPException(status_code=400, detail="No data provided for indexing")
        
        # Get updated stats
        stats = indexer.get_stats()
        results['stats'] = stats
        
        return {
            "status": "indexed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index data: {str(e)}")

@app.post("/api/indexer/index/upload")
async def upload_and_index(file: UploadFile = File(...)):
    """Upload and index a JSON file containing section or dialogue data."""
    global indexer
    
    if not indexer:
        raise HTTPException(status_code=400, detail="Indexer not initialized")
    
    try:
        # Read and parse JSON file
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        results = {}
        
        # Determine data type and index accordingly
        if 'sections' in data:
            section_index = SectionIndex.from_dict(data)
            narrative_result = indexer.index_narrative_chunks(section_index)
            results['narrative'] = narrative_result
            
        if 'scenes' in data:
            dialogue_index = DialogueIndex.from_dict(data)
            dialogue_result = indexer.index_dialogue_chunks(dialogue_index)
            results['dialogue'] = dialogue_result
        
        if not results:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Expected 'sections' or 'scenes' data."
            )
        
        # Get updated stats
        stats = indexer.get_stats()
        results['stats'] = stats
        
        return {
            "status": "indexed",
            "filename": file.filename,
            "results": results
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.post("/api/indexer/query")
async def query_indexer(request: QueryRequest):
    """Query the dual vector indexer."""
    global indexer
    
    if not indexer:
        raise HTTPException(status_code=400, detail="Indexer not initialized")
    
    try:
        if request.type == "narrative":
            if not request.query:
                raise HTTPException(status_code=400, detail="Query required for narrative search")
            result = indexer.query_narrative(request.query, request.n_results)
            
        elif request.type == "dialogue":
            if not request.query:
                raise HTTPException(status_code=400, detail="Query required for dialogue search")
            result = indexer.query_dialogue(
                query=request.query,
                n_results=request.n_results,
                character=request.character,
                dialogue_type=request.dialogue_type,
                addressee=request.addressee,
                emotion=request.emotion,
                chapter_number=request.chapter_number,
                scene_id=request.scene_id,
                setting=request.setting,
                participants=request.participants,
                personality_traits=request.personality_traits,
                emotional_state=request.emotional_state
            )
            
        elif request.type == "character":
            if not request.character:
                raise HTTPException(status_code=400, detail="Character name required for character search")
            result = indexer.get_character_dialogues(request.character, request.n_results or 10)
            
        elif request.type == "chapter":
            if request.chapter_number is None:
                raise HTTPException(status_code=400, detail="Chapter number required for chapter search")
            result = indexer.get_chapter_content(request.chapter_number)
            
        elif request.type == "theme":
            if not request.theme:
                raise HTTPException(status_code=400, detail="Theme required for theme search")
            result = indexer.get_narrative_content(request.theme, request.n_results or 5)
            
        elif request.type == "character_profiles":
            if not request.query:
                raise HTTPException(status_code=400, detail="Query required for character profile search")
            result = indexer.query_character_profiles(request.query, request.n_results or 5)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {request.type}")
        
        return result
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/api/indexer/stats")
async def get_stats():
    """Get indexer statistics."""
    global indexer
    
    if not indexer:
        raise HTTPException(status_code=400, detail="Indexer not initialized")
    
    try:
        stats = indexer.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/api/indexer/reset")
async def reset_indexer():
    """Reset the indexer (clear all data)."""
    global indexer
    
    if not indexer:
        raise HTTPException(status_code=400, detail="Indexer not initialized")
    
    try:
        indexer.reset_stores()
        stats = indexer.get_stats()
        return {
            "status": "reset",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset indexer: {str(e)}")

# Character Agent Endpoints

@app.get("/api/characters/list")
async def list_characters(refresh_cache: bool = False):
    """Get list of available characters."""
    global character_factory
    
    if not character_factory:
        raise HTTPException(status_code=400, detail="Character factory not initialized. Initialize indexer first.")
    
    try:
        available_characters = character_factory.get_available_characters()
        
        return {
            "available_characters": available_characters,
            "total_available": len(available_characters)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list characters: {str(e)}")

@app.post("/api/characters/chat")
async def chat_with_character(request: CharacterChatRequest):
    """Chat with a specific character agent."""
    global character_factory
    
    if not character_factory:
        raise HTTPException(status_code=400, detail="Character factory not initialized. Initialize indexer first.")
    
    try:
        result = character_factory.chat_with_character(
            character_name=request.character_name,
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        if not result['success']:
            status_code = 404 if 'not available' in result.get('error', '') else 500
            raise HTTPException(status_code=status_code, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/api/characters/{character_name}/info")
async def get_character_info(character_name: str):
    """Get detailed information about a character."""
    global character_factory
    
    if not character_factory:
        raise HTTPException(status_code=400, detail="Character factory not initialized. Initialize indexer first.")
    
    try:
        info = character_factory.get_character_info(character_name)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Character '{character_name}' not found")
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get character info: {str(e)}")

@app.post("/api/characters/multi-chat")
async def multi_character_chat(request: MultiCharacterChatRequest):
    """Execute a conversation between multiple characters."""
    global character_factory
    
    if not character_factory:
        raise HTTPException(status_code=400, detail="Character factory not initialized. Initialize indexer first.")
    
    try:
        result = character_factory.execute_character_conversation(
            characters=request.characters,
            prompt=request.prompt,
            max_rounds=request.max_rounds or 3
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Multi-character chat failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-character chat failed: {str(e)}")

@app.post("/api/characters/{character_name}/refresh")
async def refresh_character(character_name: str):
    """Refresh character data from vector store."""
    global character_factory
    
    if not character_factory:
        raise HTTPException(status_code=400, detail="Character factory not initialized. Initialize indexer first.")
    
    try:
        # Since we removed caching, we just indicate success
        return {
            "status": "refreshed",
            "character": character_name,
            "message": f"Character '{character_name}' data refreshed from vector store"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh character: {str(e)}")

@app.get("/api/characters/compare/{char1}/{char2}")
async def compare_characters(char1: str, char2: str):
    """Compare two characters."""
    global character_factory
    
    if not character_factory:
        raise HTTPException(status_code=400, detail="Character factory not initialized. Initialize indexer first.")
    
    try:
        comparison = character_factory.create_character_comparison(char1, char2)
        
        if not comparison['success']:
            raise HTTPException(status_code=404, detail=comparison.get('error', 'Character comparison failed'))
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Character comparison failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "indexer_initialized": indexer is not None,
        "character_factory_initialized": character_factory is not None
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "BookSouls Vector Indexer & Character Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "indexer_status": "initialized" if indexer else "not_initialized",
        "character_agents_status": "initialized" if character_factory else "not_initialized",
        "endpoints": {
            "indexer": "/api/indexer/*",
            "characters": "/api/characters/*",
            "health": "/api/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 