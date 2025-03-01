"""Embedding providers module.

This module provides implementations of various embedding providers
for converting text and other content into vector embeddings.
It includes base interfaces and specific provider implementations
for different embedding services.
"""

from .base import EmbeddingProvider
from .openai import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
