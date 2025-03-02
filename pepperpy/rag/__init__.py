"""RAG (Retrieval Augmented Generation) module.

This module provides a modular framework for building RAG applications with clear
separation between indexing, retrieval, and generation components.
"""

# Re-export public interfaces
from pepperpy.rag.public import (
    Document,
    RAGConfig,
    RAGFactory,
    RAGPipeline,
    Retriever,
    SearchQuery,
    SearchResult,
    VectorRetriever,
)

# Core components
from pepperpy.rag.base import RagComponent, RagPipeline
from pepperpy.rag.config import (
    ChunkingConfig,
    EmbeddingConfig,
    GenerationConfig,
    IndexConfig,
    RagConfig,
    RetrievalConfig,
    create_default_config,
)
from pepperpy.rag.factory import RagPipelineFactory

# Generation components
from pepperpy.rag.generation import (
    ContextAwareGenerator,
    GenerationManager,
    Generator,
    PromptGenerator,
)

# Indexing components
from pepperpy.rag.indexing import (
    Chunker,
    DocumentIndexer,
    Embedder,
    Indexer,
    IndexingManager,
)
from pepperpy.rag.pipeline import StandardRagPipeline
from pepperpy.rag.registry import RagRegistry, rag_registry

# Retrieval components
from pepperpy.rag.retrieval import (
    RetrievalManager,
    Retriever as InternalRetriever,
    SimilarityRetriever,
)
from pepperpy.rag.types import (
    Chunk,
    Document as InternalDocument,
    Embedding,
    RagComponentType,
    RagContext,
    RagResponse,
    SearchQuery as InternalSearchQuery,
    SearchResult as InternalSearchResult,
)

__all__ = [
    # Public interfaces
    "Document",
    "Retriever",
    "SearchQuery",
    "SearchResult",
    "VectorRetriever",
    "RAGPipeline",
    "RAGConfig",
    "RAGFactory",
    
    # Core components
    "RagComponent",
    "RagPipeline",
    "RagConfig",
    "ChunkingConfig",
    "EmbeddingConfig",
    "IndexConfig",
    "RetrievalConfig",
    "GenerationConfig",
    "create_default_config",
    "RagPipelineFactory",
    "StandardRagPipeline",
    "RagRegistry",
    "rag_registry",
    "RagComponentType",
    "InternalDocument",
    "Chunk",
    "Embedding",
    "InternalSearchQuery",
    "InternalSearchResult",
    "RagContext",
    "RagResponse",
    # Indexing components
    "Chunker",
    "DocumentIndexer",
    "Embedder",
    "Indexer",
    "IndexingManager",
    # Retrieval components
    "InternalRetriever",
    "RetrievalManager",
    "SimilarityRetriever",
    # Generation components
    "Generator",
    "PromptGenerator",
    "ContextAwareGenerator",
    "GenerationManager",
]
