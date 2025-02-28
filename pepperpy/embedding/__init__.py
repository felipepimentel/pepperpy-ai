"""Embedding module for vector representations.

This module provides functionality for converting text and documents into
vector embeddings for use in various applications such as RAG, semantic search,
and clustering.
"""

from .rag import (
    DocumentEmbedder,
    Embedder,
    SentenceEmbedder,
    TextEmbedder,
)

__all__ = [
    "Embedder",
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
]
