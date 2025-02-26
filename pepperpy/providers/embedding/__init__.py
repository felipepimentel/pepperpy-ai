"""Embedding providers for the Pepperpy framework."""

from .base import EmbeddingError, EmbeddingProvider
from .openai import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "EmbeddingError",
    "OpenAIEmbeddingProvider",
]
