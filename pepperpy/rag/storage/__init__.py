"""Storage module for RAG.

This module provides storage functionality for RAG, including vector store
implementations for efficient similarity search.
"""

from typing import Dict, Optional

from pepperpy.rag.interfaces import DocumentStore, VectorStore
from pepperpy.rag.models import ScoredChunk, VectorEmbedding
from pepperpy.rag.storage.providers import (
    ChromaVectorStore,
    FileVectorStore,
    MemoryVectorStore,
)

# Global manager for vector stores
_VECTOR_STORES: Dict[str, VectorStore] = {}
_DEFAULT_VECTOR_STORE: Optional[str] = None


def register_vector_store(name: str, store: VectorStore, default: bool = False) -> None:
    """Register a vector store.

    Args:
        name: The name of the store to register
        store: The store instance to register
        default: Whether this should be the default store
    """
    _VECTOR_STORES[name] = store
    if default:
        global _DEFAULT_VECTOR_STORE
        _DEFAULT_VECTOR_STORE = name


def get_vector_store(name: Optional[str] = None) -> VectorStore:
    """Get a registered vector store.

    Args:
        name: The name of the store to get, or None for the default

    Returns:
        The vector store instance

    Raises:
        ValueError: If the store is not found
    """
    if name is None:
        if _DEFAULT_VECTOR_STORE is None:
            raise ValueError("No default vector store has been registered")
        name = _DEFAULT_VECTOR_STORE

    if name not in _VECTOR_STORES:
        raise ValueError(f"Vector store '{name}' not found")

    return _VECTOR_STORES[name]


def list_vector_stores() -> Dict[str, VectorStore]:
    """Get all registered vector stores.

    Returns:
        A dictionary of registered vector stores
    """
    return _VECTOR_STORES.copy()


__all__ = [
    # Core types
    "VectorEmbedding",
    "ScoredChunk",
    "VectorStore",
    "DocumentStore",
    # Providers
    "MemoryVectorStore",
    "FileVectorStore",
    "ChromaVectorStore",
    # Management functions
    "register_vector_store",
    "get_vector_store",
    "list_vector_stores",
]
