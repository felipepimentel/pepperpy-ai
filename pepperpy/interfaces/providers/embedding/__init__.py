"""Public Interface for embedding providers

This module provides a stable public interface for embedding providers.
It exposes the core embedding provider abstractions and implementations
that are considered part of the public API.

Classes:
    EmbeddingProvider: Base class for embedding providers
    OpenAIEmbeddingProvider: OpenAI implementation of embedding provider
"""

# Import public classes and functions from the implementation
from pepperpy.embedding.providers.base import EmbeddingProvider
from pepperpy.embedding.providers.openai import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
