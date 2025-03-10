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
from pepperpy.rag.storage.providers.file import FileVectorStore

# Try to import providers, making optional ones conditional
from pepperpy.rag.storage.providers.memory import MemoryVectorStore

# Try to import Chroma provider if available
try:
    from pepperpy.rag.storage.providers.chroma import ChromaVectorStore

    _has_chroma = True
except ImportError:
    _has_chroma = False

__all__ = [
    # Core types
    "ScoredChunk",
    "VectorEmbedding",
    "VectorStore",
    "VectorStoreManager",
    "get_vector_store_manager",
    # Vector store implementations
    "MemoryVectorStore",
    "FileVectorStore",
]

# Add optional providers to __all__ if available
if _has_chroma:
    __all__.append("ChromaVectorStore")
