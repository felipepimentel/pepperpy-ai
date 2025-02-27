"""RAG (Retrieval Augmented Generation) package."""

from .base import (
    Augmenter,
    Chunker,
    Embedder,
    Indexer,
    RagComponent,
    RagPipeline,
    Retriever,
)
from .chunkers import HTMLChunker, RecursiveChunker, TextChunker
from .config import (
    AugmentationConfig,
    ChunkingConfig,
    EmbeddingConfig,
    IndexConfig,
    RagConfig,
    RetrievalConfig,
)
from .defaults import register_default_components
from .embedders import (
    BatchedEmbedder,
    CachedEmbedder,
    HybridEmbedder,
    TransformerEmbedder,
)
from .factory import RagPipelineFactory
from .indexers import AnnoyIndexer, FaissIndexer, HybridIndexer
from .pipeline import StandardRagPipeline
from .registry import registry
from .types import (
    Chunk,
    ChunkType,
    Document,
    Embedding,
    RagContext,
    RagResponse,
    SearchQuery,
    SearchResult,
)

# Register default components
register_default_components()

__all__ = [
    # Base interfaces
    "RagComponent",
    "RagPipeline",
    "Chunker",
    "Embedder",
    "Indexer",
    "Retriever",
    "Augmenter",
    # Configuration
    "RagConfig",
    "ChunkingConfig",
    "EmbeddingConfig",
    "IndexConfig",
    "RetrievalConfig",
    "AugmentationConfig",
    # Pipeline
    "StandardRagPipeline",
    "RagPipelineFactory",
    # Registry
    "registry",
    # Types
    "ChunkType",
    "Chunk",
    "Document",
    "Embedding",
    "SearchQuery",
    "SearchResult",
    "RagContext",
    "RagResponse",
    # Chunker implementations
    "TextChunker",
    "RecursiveChunker",
    "HTMLChunker",
    # Embedder implementations
    "TransformerEmbedder",
    "CachedEmbedder",
    "BatchedEmbedder",
    "HybridEmbedder",
    # Indexer implementations
    "FaissIndexer",
    "AnnoyIndexer",
    "HybridIndexer",
]
