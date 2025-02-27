"""RAG embedding package.

This package provides functionality for converting text and documents into
vector embeddings for semantic search and retrieval.
"""

from .embedders import (
    Embedder,
    TextEmbedder,
    DocumentEmbedder,
    SentenceEmbedder,
)

__all__ = [
    # Base class
    "Embedder",
    # Specific embedders
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
]