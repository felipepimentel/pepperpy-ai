"""Embedding provider implementations.

This module provides concrete implementations of the EmbeddingProvider interface.
"""

from .local import LocalEmbeddingProvider
from .openai import OpenAIEmbeddingProvider

__all__ = [
    "LocalEmbeddingProvider",
    "OpenAIEmbeddingProvider",
] 