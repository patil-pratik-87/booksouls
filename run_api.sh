#!/bin/bash
# BookSouls API Server Launcher Script

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Set environment variables if not already set
export BOOKSOULS_VECTOR_DIR="${BOOKSOULS_VECTOR_DIR:-./vector_stores}"

echo "🚀 Starting BookSouls Vector Indexer API..."
echo "📁 Vector stores directory: $BOOKSOULS_VECTOR_DIR"
echo "🌐 Server will be available at: http://localhost:8000"
echo "📖 API docs available at: http://localhost:8000/docs"

# Run the API server
python3 run_api.py 