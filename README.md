# BookSouls Chapter Chunker

A Python library for extracting chapter-level content from PDF books and chunking them into 400-token segments using RecursiveCharacterTextSplitter.

## Features

- 📚 **Chapter Detection**: Automatically detects chapters in PDF books using multiple regex patterns
- 🔧 **400-Token Chunking**: Uses LangChain's RecursiveCharacterTextSplitter for consistent 400-token chunks
- 📄 **PDF Processing**: Built on PyMuPDF (fitz) for robust PDF text extraction
- 🎯 **Dual Output**: Provides both chapter-level and token-level chunks
- ⚡ **Fast Processing**: Efficient page-by-page processing with real-time progress

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.8+
- PyMuPDF (fitz)
- LangChain text splitters
- tiktoken

## Quick Start

```python
from ChunkAccuracyTester import create_chapter_chunker

# Create chunker
chunker = create_chapter_chunker("path/to/your/book.pdf")

# Extract chapters
chapters = chunker.extract_chapters_from_pdf()

# Get processing-ready chunks
chapter_chunks = chunker.get_chapter_chunks_for_processing(chapters)  # Full chapters
token_chunks = chunker.get_token_chunks_for_processing(chapters)     # 400-token chunks

print(f"Extracted {len(chapters)} chapters")
print(f"Generated {len(token_chunks)} token-level chunks")
```

## Usage

### Basic Example

```python
from ChunkAccuracyTester import ChunkingAccuracyTester

pdf_path = "fellowship_of_the_ring.pdf"
chunker = ChunkingAccuracyTester(pdf_path)

# Extract chapters
chapters = chunker.extract_chapters_from_pdf()

# Print summary
chunker.print_chapter_summary(chapters)
```

### Chapter Structure

Each `ChapterChunk` contains:

```python
@dataclass  
class ChapterChunk:
    chapter_number: int        # Chapter number (1, 2, 3...)
    chapter_title: str         # Chapter title text
    content: str              # Full chapter text
    chunks: List[str]         # 400-token chunks with 30-token overlap
    start_page: int           # Starting page number
    end_page: int             # Ending page number  
    word_count: int           # Total words in chapter
```

### Token Chunking Configuration

The chunker uses optimized settings for book content:

- **Chunk Size**: 400 tokens
- **Chunk Overlap**: 30 tokens
- **Separators**: `["\n\n", "\n", ". ", " ", ""]`
- **Token Counting**: tiktoken with cl100k_base encoding

## Supported Chapter Formats

The chunker detects chapters using these patterns:

- `Chapter 1: The Title`
- `CHAPTER 1: THE TITLE`
- `Ch. 1: Title`
- `1. Title`

## Example Output

```
📖 Processing PDF: fellowship_of_the_ring.pdf
📄 Total pages: 531
📚 Found Chapter 1: A Long-expected Party (page 23)
   📝 Chapter 1: 18 chunks (~400 tokens each), 6,847 words
📚 Found Chapter 2: The Shadow of the Past (page 45)
   📝 Chapter 2: 22 chunks (~400 tokens each), 8,234 words
✅ Extracted 22 chapters in 3.45s

🔄 READY FOR PROCESSING:
📚 Chapter-level chunks: 22
📝 Token-level chunks (400 tokens): 387
✨ Ready for BookSouls dual-index architecture!
```

## Use Cases

- **Book Analysis**: Extract structured content for literary analysis
- **Search Indexing**: Create searchable chapter-level and token-level indexes
- **Content Processing**: Feed consistent chunks to embedding models
- **Dual Architecture**: Support both high-level (chapter) and granular (token) retrieval

## Architecture

Perfect for dual-index systems where you need:
1. **Chapter-level context** for broad understanding
2. **Token-level precision** for specific information retrieval

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Changelog

### v1.0.0 (2024-07-21)
- Initial release
- Chapter detection with multiple patterns
- 400-token chunking with RecursiveCharacterTextSplitter
- Dual output methods (chapter-level and token-level)
- Clean, evaluation-free API