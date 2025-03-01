"""Embedding providers module.

This module provides implementations of various embedding providers
for converting text into vector embeddings.
"""

from pepperpy.embedding.base import BaseEmbedding, EmbeddingError
from pepperpy.embedding.registry import register_embedding

from .base import EmbeddingProvider
from .openai import OpenAIEmbeddingProvider

# Register providers
register_embedding("openai", OpenAIEmbeddingProvider)

__all__ = [
    "EmbeddingError",
    "EmbeddingProvider",
    "BaseEmbedding",
    "OpenAIEmbeddingProvider",
]
