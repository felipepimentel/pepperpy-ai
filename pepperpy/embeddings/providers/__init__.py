"""Embedding provider implementations.

This module provides concrete implementations of the EmbeddingProvider interface.
"""

from .local import LocalProvider
from .numpy_provider import NumpyProvider
from .openai import OpenAIEmbeddingProvider

__all__ = [
    "LocalProvider",
    "NumpyProvider",
    "OpenAIEmbeddingProvider",
]
