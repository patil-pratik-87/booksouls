"""
FastAPI Backend for BookSouls Dual Vector Indexer

Provides REST API endpoints to connect the React UI with the dual vector indexer.
Supports narrative and dialogue vector stores with various query types.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
import traceback
import dotenv

# BookSouls imports
from ..indexers.dual_vector_indexer import DualVectorIndexer, create_dual_indexer
from ..indexers.config import get_openai_config
from ..chunkers.chapter_chunker import SectionIndex
from ..chunkers.dialogue_chunker import DialogueIndex

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

# Global indexer instance
indexer: Optional[DualVectorIndexer] = None

# Request models
class QueryRequest(BaseModel):
    type: str  # 'narrative', 'dialogue', 'character', 'chapter', 'theme'
    query: Optional[str] = None
    character: Optional[str] = None
    chapter_number: Optional[int] = None
    theme: Optional[str] = None
    n_results: Optional[int] = None

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

@app.post("/api/indexer/initialize")
async def initialize_indexer(request: InitializeRequest = InitializeRequest()):
    """Initialize the dual vector indexer."""
    global indexer
    
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
        
        # Get current stats
        stats = indexer.get_stats()
        
        return {
            "status": "initialized",
            "config": {
                "base_persist_dir": config.base_persist_dir,
                "narrative_collection": config.narrative_collection,
                "dialogue_collection": config.dialogue_collection,
            },
            "stats": stats
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
            result = indexer.query_dialogue(request.query, request.n_results)
            
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
            result = indexer.get_thematic_content(request.theme, request.n_results or 5)
            
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "indexer_initialized": indexer is not None
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "BookSouls Vector Indexer API",
        "version": "1.0.0",
        "docs": "/docs",
        "indexer_status": "initialized" if indexer else "not_initialized"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 