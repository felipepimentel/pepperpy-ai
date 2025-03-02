"""RAG (Retrieval Augmented Generation) module.

This module provides a modular framework for building RAG applications with clear
separation between indexing, retrieval, and generation components.
"""

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
    Retriever,
    SimilarityRetriever,
)
from pepperpy.rag.types import (
    Chunk,
    Document,
    Embedding,
    RagComponentType,
    RagContext,
    RagResponse,
    SearchQuery,
    SearchResult,
)

__all__ = [
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
    "Document",
    "Chunk",
    "Embedding",
    "SearchQuery",
    "SearchResult",
    "RagContext",
    "RagResponse",
    # Indexing components
    "Chunker",
    "DocumentIndexer",
    "Embedder",
    "Indexer",
    "IndexingManager",
    # Retrieval components
    "Retriever",
    "RetrievalManager",
    "SimilarityRetriever",
    # Generation components
    "Generator",
    "PromptGenerator",
    "ContextAwareGenerator",
    "GenerationManager",
]
