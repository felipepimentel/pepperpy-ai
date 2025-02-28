"""RAG (Retrieval Augmented Generation) package."""

from .base import (
    RagComponent,
    RagPipeline,
)
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
    DocumentEmbedder,
    Embedder,
    SentenceEmbedder,
    TextEmbedder,
)
from .factory import RagPipelineFactory
from .indexers import (
    HybridIndexer,
    Indexer,
    TextIndexer,
    VectorIndexer,
)
from .optimizations import (
    # Compression
    DimensionalityReducer,
    DiversityPruner,
    # Caching
    EmbeddingCache,
    QualityPruner,
    QuantizationCompressor,
    QueryCache,
    # Pruning
    RedundancyPruner,
    ResultCache,
    VectorCompressor,
)
from .pipeline import StandardRagPipeline

# Import from new consolidated modules
from .preprocessing import (
    # Augmentation
    Augmenter,
    # Chunking
    Chunker,
    ContextAugmenter,
    ParagraphChunker,
    QueryAugmenter,
    ResultAugmenter,
    SentenceChunker,
    TextChunker,
    TokenChunker,
)
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
    "TokenChunker",
    "SentenceChunker",
    "ParagraphChunker",
    # Embedder implementations
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
    # Indexer implementations
    "VectorIndexer",
    "TextIndexer",
    "HybridIndexer",
    # Augmenter implementations
    "QueryAugmenter",
    "ResultAugmenter",
    "ContextAugmenter",
    # Optimization implementations
    # Caching
    "EmbeddingCache",
    "QueryCache",
    "ResultCache",
    # Compression
    "DimensionalityReducer",
    "VectorCompressor",
    "QuantizationCompressor",
    # Pruning
    "RedundancyPruner",
    "QualityPruner",
    "DiversityPruner",
]
