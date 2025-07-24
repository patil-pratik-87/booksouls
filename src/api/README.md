# BookSouls Vector Indexer API

FastAPI backend that connects the dual vector indexer to the React UI, providing REST endpoints for indexing and querying book content.

## Features

- **Dual Vector Stores**: Separate optimized stores for narrative and dialogue content
- **Multiple Query Types**: Support for narrative, dialogue, character, chapter, and theme queries
- **File Upload**: Index content by uploading JSON files
- **OpenAI Integration**: Optional OpenAI embeddings for enhanced semantic search
- **CORS Support**: Ready for React frontend integration

## API Endpoints

### Core Endpoints

- `POST /api/indexer/initialize` - Initialize the vector indexer
- `POST /api/indexer/query` - Query the vector stores
- `GET /api/indexer/stats` - Get indexer statistics
- `POST /api/indexer/reset` - Reset all vector stores

### Data Management

- `POST /api/indexer/index` - Index data from JSON
- `POST /api/indexer/index/upload` - Upload and index JSON files

### Utility

- `GET /api/health` - Health check
- `GET /docs` - Interactive API documentation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server:**
   ```bash
   python3 run_api.py
   ```

3. **Test the API:**
   ```bash
   python3 test_api_client.py
   ```

4. **Open the interactive docs:**
   Open http://localhost:8000/docs in your browser

## Query Types

### Narrative Query
Search through narrative content optimized for thematic and structural retrieval:
```json
{
  "type": "narrative",
  "query": "character development and growth",
  "n_results": 5
}
```

### Dialogue Query
Search through dialogue content with character focus:
```json
{
  "type": "dialogue", 
  "query": "emotional conversation between characters",
  "n_results": 10
}
```

### Character Query
Get all dialogues for a specific character:
```json
{
  "type": "character",
  "character": "Elizabeth",
  "n_results": 15
}
```

### Chapter Query
Retrieve all content from a specific chapter:
```json
{
  "type": "chapter",
  "chapter_number": 5
}
```

### Theme Query
Search for content by theme:
```json
{
  "type": "theme",
  "theme": "love and relationships"
}
```

## Configuration

### Basic Configuration
The API uses ChromaDB's default embeddings by default.

### OpenAI Configuration
For enhanced semantic search with OpenAI embeddings:

1. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```

2. Initialize with OpenAI embeddings:
   ```json
   {
     "use_openai": true
   }
   ```

## Integration with UI

The API is designed to work with the React UI in `ui/index-visualizer/`. The frontend expects these specific endpoints and response formats.

### CORS Configuration
The API is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Create React App)

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (missing parameters, etc.)
- `500` - Internal server error

Error responses include descriptive messages:
```json
{
  "detail": "Indexer not initialized"
}
```

## Development

### Running in Development Mode
```bash
python3 run_api.py
```

The server runs with auto-reload enabled, so changes to the code will automatically restart the server.

### Testing
Use the provided test client:
```bash
python3 test_api_client.py
```

### API Documentation
Interactive documentation is available at http://localhost:8000/docs when the server is running. 