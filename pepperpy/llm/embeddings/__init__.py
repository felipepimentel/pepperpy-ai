"""Embedding capabilities for PepperPy.

This module provides interfaces and implementations for text embeddings,
supporting vector representations for semantic search and similarity.
"""

from pepperpy.llm.embeddings.provider import EmbeddingConfig, EmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "EmbeddingConfig",
]
