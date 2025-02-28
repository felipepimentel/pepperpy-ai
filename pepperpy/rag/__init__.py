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
from .embedding import (
    DocumentEmbedder,
    Embedder,
    MultiModalEmbedder,
    TextEmbedder,
)
from .factory import RagPipelineFactory
from .indexing import (
    HybridIndexer,
    Indexer,
    TextIndexer,
    VectorIndexer,
)
from .optimization import (
    # Compression
    DimensionalityReducer,
    # Pruning
    DiversityPruner,
    QualityPruner,
    QuantizationCompressor,
    RedundancyPruner,
    VectorCompressor,
    VectorPruner,
)
from .pipeline import StandardRagPipeline
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
from .retrieval_system import (
    HybridRetriever,
    Retriever,
    TextRetriever,
    VectorRetriever,
)
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
    "MultiModalEmbedder",
    # Indexer implementations
    "VectorIndexer",
    "TextIndexer",
    "HybridIndexer",
    # Retriever implementations
    "VectorRetriever",
    "TextRetriever",
    "HybridRetriever",
    # Augmenter implementations
    "QueryAugmenter",
    "ResultAugmenter",
    "ContextAugmenter",
    # Optimization implementations
    # Compression
    "DimensionalityReducer",
    "VectorCompressor",
    "QuantizationCompressor",
    # Pruning
    "RedundancyPruner",
    "QualityPruner",
    "DiversityPruner",
    "VectorPruner",
]
