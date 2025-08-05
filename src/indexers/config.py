"""
Indexer Configuration for BookSouls Vector Stores

Simple configuration for dual vector indexing currently used in DualVectorIndexer.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
import os

class EmbeddingFunction(Enum):
    """Available embedding functions for ChromaDB."""
    DEFAULT = "default"  # ChromaDB's default embedding function
    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"


@dataclass
class EmbeddingConfig:
    """Embedding function configuration."""
    function_type: EmbeddingFunction = EmbeddingFunction.DEFAULT
    api_key: Optional[str] = None  # For OpenAI embeddings
    model_kwargs: dict = None  # Additional model parameters

    def __post_init__(self):
        if self.model_kwargs is None:
            self.model_kwargs = {}


@dataclass
class QueryConfig:
    """Query hyperparameters for ChromaDB."""
    # Basic query params
    n_results: int = 5
    
    # Advanced query params (ChromaDB supports these in query method)
    include: list = None  # What to include in results: ["metadatas", "documents", "distances"]
    
    def __post_init__(self):
        if self.include is None:
            self.include = ["metadatas", "documents", "distances"]


@dataclass
class IndexerConfig:
    """Configuration for dual vector indexer."""
    # Directory settings
    base_persist_dir: str = "./vector_stores"
    narrative_collection: str = "narrative"
    dialogue_collection: str = "dialogue"
    
    # ChromaDB settings
    anonymized_telemetry: bool = False
    allow_reset: bool = True
    
    # Embedding configurations
    narrative_embedding: EmbeddingConfig = None
    dialogue_embedding: EmbeddingConfig = None
    
    # Query configurations
    narrative_query: QueryConfig = None
    dialogue_query: QueryConfig = None
    
    # Legacy query defaults (for backward compatibility)
    default_narrative_results: int = 5
    default_dialogue_results: int = 5
    
    def __post_init__(self):
        if self.narrative_embedding is None:
            self.narrative_embedding = EmbeddingConfig()
        if self.dialogue_embedding is None:
            self.dialogue_embedding = EmbeddingConfig()
        if self.narrative_query is None:
            self.narrative_query = QueryConfig(n_results=self.default_narrative_results)
        if self.dialogue_query is None:
            self.dialogue_query = QueryConfig(n_results=self.default_dialogue_results)


# Default configuration
DEFAULT_CONFIG = IndexerConfig()


def get_default_config() -> IndexerConfig:
    """Get default indexer configuration."""
    return DEFAULT_CONFIG

def get_openai_config(api_key: str = None) -> IndexerConfig:
    """Get OpenAI-based embedding configuration."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable is required or pass api_key parameter")       
    return IndexerConfig(
        narrative_embedding=EmbeddingConfig(
            function_type=EmbeddingFunction.OPENAI_3_LARGE,
            api_key=api_key
        ),
        dialogue_embedding=EmbeddingConfig(
            function_type=EmbeddingFunction.OPENAI_3_LARGE,
            api_key=api_key
        ),
        narrative_query=QueryConfig(n_results=8),
        dialogue_query=QueryConfig(n_results=20)
    )