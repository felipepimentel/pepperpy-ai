"""Embedding module for PepperPy.

This module provides embedding capabilities for text and documents.
"""

# Re-export public interfaces
# Import internal implementations
from pepperpy.embedding.base import BaseEmbedding
from pepperpy.embedding.factory import create_embedding
from pepperpy.embedding.public import (
    CachedEmbedder,
    DocumentEmbedder,
    Embedder,
    EmbeddingProvider,
    SentenceEmbedder,
    TextEmbedder,
)
from pepperpy.embedding.types import EmbeddingType

__all__ = [
    # Public interfaces
    "Embedder",
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
    "EmbeddingProvider",
    "CachedEmbedder",
    # Implementation classes
    "BaseEmbedding",
    "create_embedding",
    "EmbeddingType",
]
