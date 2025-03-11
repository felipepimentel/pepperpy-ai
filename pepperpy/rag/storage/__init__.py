"""
PepperPy RAG Storage Module.

Este módulo contém os componentes de armazenamento para o sistema RAG.
"""

from __future__ import annotations

from pepperpy.rag.storage.core import (
    ScoredChunk,
    VectorEmbedding,
    VectorStore,
    VectorStoreManager,
    get_vector_store_manager,
)
from pepperpy.rag.storage.providers import (
    ChromaVectorStore,
    FileVectorStore,
    MemoryVectorStore,
)

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
    "ChromaVectorStore",
]
