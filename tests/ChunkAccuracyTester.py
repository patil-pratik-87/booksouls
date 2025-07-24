import time
import fitz
from typing import Dict, List
import re
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

@dataclass
class ChapterChunk:
    chapter_number: int
    chapter_title: str
    content: str
    chunks: List[str]  # 400-token chunks using RecursiveTextSplitter
    start_page: int
    end_page: int
    word_count: int

class ChunkingAccuracyTester:
    def __init__(self, pdf_path: str, chunk_size: int = 400, chunk_overlap: int = 30):
        """
        Chapter-level chunking tester using PyMuPDF (fitz) for PDF processing.
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = None
        
        # Initialize text splitter for 400-token chunks
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
        
    def extract_chapters_from_pdf(self) -> List[ChapterChunk]:
        """
        Extract chapter-level chunks from PDF using fitz.
        Returns the extracted chapters.
        """
        start_time = time.time()
        
        try:
            self.doc = fitz.open(self.pdf_path)
            chapters = []
            
            # Chapter detection patterns
            chapter_patterns = [
                r'Chapter\s+(\d+)[:\s]*(.{0,100})',  # Chapter N: Title
                r'CHAPTER\s+(\d+)[:\s]*(.{0,100})',  # CHAPTER N: Title
                r'Ch\.\s*(\d+)[:\s]*(.{0,100})',     # Ch. N: Title
                r'^(\d+)\.\s+(.{0,100})',            # N. Title
            ]
            
            current_chapter = None
            chapter_content = []
            
            print(f"Processing PDF: {self.pdf_path}")
            print(f"Total pages: {self.doc.page_count}")
            
            for page_num in range(self.doc.page_count):
                page = self.doc[page_num]
                text = page.get_text()
                
                # Check for chapter start
                chapter_match = None
                for pattern in chapter_patterns:
                    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                    if match:
                        chapter_match = match
                        break
                
                # If we found a new chapter, save the previous one
                if chapter_match and current_chapter is not None:
                    self._finalize_chapter(current_chapter, chapter_content, chapters, page_num - 1)
                    chapter_content = []
                
                # Start new chapter if found
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                    chapter_title = chapter_match.group(2).strip() if len(chapter_match.groups()) > 1 else f"Chapter {chapter_num}"
                    
                    current_chapter = {
                        'number': chapter_num,
                        'title': chapter_title,
                        'start_page': page_num + 1  # 1-indexed
                    }
                    print(f"Found Chapter {chapter_num}: {chapter_title} (page {page_num + 1})")
                
                # Add content to current chapter
                if current_chapter is not None:
                    chapter_content.append(text)
            
            # Finalize the last chapter
            if current_chapter is not None:
                self._finalize_chapter(current_chapter, chapter_content, chapters, self.doc.page_count)
            
            processing_time = time.time() - start_time
            print(f"Extracted {len(chapters)} chapters in {processing_time:.2f}s")
            
            return chapters
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return []
        
        finally:
            if self.doc:
                self.doc.close()

    def _finalize_chapter(self, chapter_info: Dict, content_pages: List[str], 
                         chapters: List[ChapterChunk], end_page: int):
        """Finalize a chapter and add it to the chapters list."""
        full_content = '\n'.join(content_pages)
        word_count = len(full_content.split())
        
        # Use RecursiveTextSplitter to create 400-token chunks
        chunks = self.text_splitter.split_text(full_content)
        
        chapter_chunk = ChapterChunk(
            chapter_number=chapter_info['number'],
            chapter_title=chapter_info['title'],
            content=full_content,
            chunks=chunks,
            start_page=chapter_info['start_page'],
            end_page=end_page,
            word_count=word_count
        )
        
        chapters.append(chapter_chunk)
        print(f"   Chapter {chapter_info['number']}: {len(chunks)} chunks (~400 tokens each), {word_count} words")

    def print_chapter_summary(self, chapters: List[ChapterChunk]):
        """Print a summary of extracted chapters."""
        print(f"\nCHAPTER EXTRACTION SUMMARY")
        print("=" * 50)
        
        for chapter in chapters:
            print(f"Chapter {chapter.chapter_number}: {chapter.chapter_title}")
            print(f"  Pages: {chapter.start_page}-{chapter.end_page}")
            print(f"  Chunks: {len(chapter.chunks)} (~400 tokens each)")
            print(f"  📊 Words: {chapter.word_count:,}")
            
            # Show first chunk as preview
            if chapter.chunks:
                preview = chapter.chunks[0][:100] + "..." if len(chapter.chunks[0]) > 100 else chapter.chunks[0]
                print(f"  Preview: {preview}")
            print()

    def get_chapter_chunks_for_processing(self, chapters: List[ChapterChunk]) -> List[str]:
        """
        Convert chapter chunks to text chunks ready for further processing.
        Returns a list of text chunks (one per chapter).
        """
        return [chapter.content for chapter in chapters]

    def get_token_chunks_for_processing(self, chapters: List[ChapterChunk]) -> List[str]:
        """
        Convert chapter chunks to token-level chunks for processing.
        Returns a list of 400-token chunks across all chapters.
        """
        all_chunks = []
        for chapter in chapters:
            all_chunks.extend(chapter.chunks)
        return all_chunks


# Factory function for easy usage
def create_chapter_chunker(pdf_path: str) -> ChunkingAccuracyTester:
    """Factory function to create a chapter-level chunker."""
    return ChunkingAccuracyTester(pdf_path)

# Example usage
if __name__ == "__main__":
    pdf_path = "./data/sample_books/j-r-r-tolkien-lord-of-the-rings-01-the-fellowship-of-the-ring-retail-pdf.pdf"
    print("BookSouls Chapter-Level Chunking")
    print("=" * 60)
    
    # Create chunker
    chunker = create_chapter_chunker(pdf_path)
    
    # Extract chapters
    chapters = chunker.extract_chapters_from_pdf()
    
    if chapters:
        # Show chapter summary
        chunker.print_chapter_summary(chapters)
        
        # Example: Get chunks ready for further processing
        chapter_chunks = chunker.get_chapter_chunks_for_processing(chapters)
        token_chunks = chunker.get_token_chunks_for_processing(chapters)
        
        print(f"\nREADY FOR PROCESSING:")
        print(f"Chapter-level chunks: {len(chapter_chunks)}")
        print(f"Token-level chunks (400 tokens): {len(token_chunks)}")
        print(f"✨ Ready for BookSouls dual-index architecture!")
        
    else:
        print("ERROR: No chapters extracted. Check PDF format or chapter detection patterns!")