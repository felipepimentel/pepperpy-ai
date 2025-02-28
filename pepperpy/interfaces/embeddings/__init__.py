"""
Public Interface for embeddings

This module provides a stable public interface for the embeddings functionality.
It exposes the core embedding abstractions and implementations that are
considered part of the public API.

Classes:
    Embedder: Base class for embedding functionality
    TextEmbedder: Embedder for text content
    DocumentEmbedder: Embedder for document content
    SentenceEmbedder: Embedder for sentence-level content
    EmbeddingProvider: Base class for embedding providers
"""

# Import public classes and functions from the implementation
from pepperpy.embedding import (
    DocumentEmbedder,
    Embedder,
    SentenceEmbedder,
    TextEmbedder,
)
from pepperpy.embedding.providers import EmbeddingProvider
from pepperpy.embedding.providers.openai import OpenAIEmbeddingProvider

__all__ = [
    "Embedder",
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
