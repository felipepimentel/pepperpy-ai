"""Embedding module for vector representations.

This module provides functionality for converting text and documents into
vector embeddings for use in various applications such as RAG, semantic search,
and clustering.
"""

from .base import BaseEmbedding, EmbeddingError
from .factory import create_embedding
from .registry import (
    register_embedding,
    get_embedding_class,
    list_embeddings,
    get_embedding_registry,
)
from .types import (
    EmbeddingType,
    EmbeddingDimension,
    EmbeddingConfig,
    EmbeddingResult,
)
from .rag import (
    DocumentEmbedder,
    Embedder,
    SentenceEmbedder,
    TextEmbedder,
)

__all__ = [
    # Base classes
    "BaseEmbedding",
    "EmbeddingError",
    
    # Factory
    "create_embedding",
    
    # Registry
    "register_embedding",
    "get_embedding_class",
    "list_embeddings",
    "get_embedding_registry",
    
    # Types
    "EmbeddingType",
    "EmbeddingDimension",
    "EmbeddingConfig",
    "EmbeddingResult",
    
    # RAG embedders
    "Embedder",
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
]
