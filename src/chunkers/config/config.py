# config.py
from dataclasses import dataclass, field
from typing import List, Literal

# Allowed semantic types for classification prompts
SemanticType = Literal["narrative", "dialogue", "description", "action", "other"]

@dataclass
class ChapterChunkerConfig:
    # ── LLM settings ───────────────────────────────────────────────
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.1
    top_p: float = 0.7
    max_tokens: int = 400         # for chapter TL;DR
    request_timeout: int = 30             # seconds

    # ── Section-level rules ────────────────────────────────────────
    min_section_tokens: int = 100         # skip micro-chunks
    semantic_types: List[SemanticType] = field(
        default_factory=lambda: ["narrative", "dialogue", "description", "action"]
    )


    # ── Performance knobs ──────────────────────────────────────────
    # concurrency: int = 8                  # max concurrent LLM calls
    # cache_path: str = ".llm_cache.sqlite" # set to "" to disable
    # use_async: bool = True                # flip to False for simple serial run

    # ── Misc ───────────────────────────────────────────────────────
    verbose: bool = True                  # print progress & timing

    # Derived helper (optional)
    def as_openai_kwargs(self) -> dict:
        """Return the kwargs dict expected by openai.ChatCompletion.create()."""
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "timeout": self.request_timeout,
        }


@dataclass
class DialogueChunkerConfig:
    # ── Model settings ─────────────────────────────────────────────
    model_type: Literal["ollama", "openai"] = "openai"
    model_name: str = None  # Auto-selected based on model_type if None
    api_key: str = None     # OpenAI API key (uses env var if None)
    
    # ── LLM parameters ─────────────────────────────────────────────
    temperature: float = 0.1
    top_p: float = 0.7
    max_tokens: int = 1200          # Response length limit
    request_timeout: int = 180      # API timeout in seconds
    
    # ── Dialogue extraction ────────────────────────────────────────
    custom_prompt: str = None       # Custom extraction prompt (uses default if None)
    skip_non_dialogue: bool = True  # Skip chunks without dialogue markers
    
    # ── Character analysis settings ────────────────────────────────
    top_characters_per_chapter: int = 4    # Number of top characters to analyze per chapter
    max_sample_dialogues: int = 7        # Max dialogue samples for character analysis
    
    # ── Ollama-specific settings ───────────────────────────────────
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_stop_tokens: List[str] = field(
        default_factory=lambda: ["Text:", "Example:", "\\n\\n"]
    )
    
    # ── OpenAI-specific settings ───────────────────────────────────
    use_json_mode: bool = True      # Use structured JSON response format
    
    # ── Misc ───────────────────────────────────────────────────────
    verbose: bool = True            # print progress & timing
    
    def get_default_model_name(self) -> str:
        """Get default model name based on model_type."""
        if self.model_type == "ollama":
            return "llama3.1:8b-instruct-q4_0"
        else:
            return "gpt-4o-mini"
    
    def as_openai_kwargs(self) -> dict:
        """Return the kwargs dict expected by openai.ChatCompletion.create()."""
        kwargs = {
            "model": self.model_name or self.get_default_model_name(),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "timeout": self.request_timeout,
        }
        if self.use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs


@dataclass 
class PDFExtractorConfig:
    # ── Chunking parameters ────────────────────────────────────────
    chunk_size: int = 600          # Default chunk size in tokens
    chunk_overlap: int = 50         # Overlap between chunks in tokens
    
    # ── Chapter detection patterns ─────────────────────────────────
    chapter_patterns: List[str] = field(
        default_factory=lambda: [
            r'Chapter\s+(\d+)[:\s]*(.{0,100})',  # Chapter N: Title
            r'CHAPTER\s+(\d+)[:\s]*(.{0,100})',  # CHAPTER N: Title  
            r'Ch\.\s*(\d+)[:\s]*(.{0,100})',     # Ch. N: Title
            r'^(\d+)\.\s+(.{0,100})',            # N. Title
        ]
    )
    
    # ── Text splitting separators ──────────────────────────────────
    text_separators: List[str] = field(
        default_factory=lambda: [
            "\n\n\n",    # Strong paragraph breaks
            "\n\n",      # Paragraph breaks
            "\n",        # Line breaks
            ". ",        # Sentence breaks
            "! ",        # Exclamation breaks
            "? ",        # Question breaks
            "; ",        # Semicolon breaks
            ", ",        # Comma breaks
            " ",         # Word breaks
            ""           # Character breaks
        ]
    )
    
    # ── Processing options ─────────────────────────────────────────
    skip_empty_pages: bool = True    # Skip pages with minimal content
    min_page_chars: int = 50        # Minimum characters per page to process
    
    # ── Misc ───────────────────────────────────────────────────────
    verbose: bool = True            # print progress & timing