"""Embedding providers module.

This module provides functionality for generating embeddings from text.
"""

from pepperpy.rag.providers.embedding.base import BaseEmbeddingProvider
from pepperpy.rag.providers.embedding.mock import MockEmbeddingProvider
from pepperpy.rag.providers.embedding.openai import OpenAIEmbeddingProvider

__all__ = [
    "BaseEmbeddingProvider",
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
