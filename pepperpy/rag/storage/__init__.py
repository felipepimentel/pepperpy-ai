"""Vector storage module for RAG.

This module provides functionality for vector storage in RAG,
including vector representation, storage, and retrieval.
"""

from pepperpy.rag.storage.core import (
    ScoredChunk,
    VectorEmbedding,
    VectorStore,
    VectorStoreManager,
    get_vector_store_manager,
)

__all__ = [
    "ScoredChunk",
    "VectorEmbedding",
    "VectorStore",
    "VectorStoreManager",
    "get_vector_store_manager",
]
