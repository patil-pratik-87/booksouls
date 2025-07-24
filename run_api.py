#!/usr/bin/env python3
"""
BookSouls API Server Launcher

Run the FastAPI server for the BookSouls dual vector indexer.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # Set default vector store directory if not specified
    if not os.getenv("BOOKSOULS_VECTOR_DIR"):
        os.environ["BOOKSOULS_VECTOR_DIR"] = str(Path.cwd() / "vector_stores")
    
    print("🚀 Starting BookSouls Vector Indexer API...")
    print(f"📁 Vector stores directory: {os.getenv('BOOKSOULS_VECTOR_DIR', './vector_stores')}")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📖 API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"]
    ) 