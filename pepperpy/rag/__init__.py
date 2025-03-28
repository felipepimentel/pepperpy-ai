"""Retrieval Augmented Generation (RAG) Module.

This module provides the tools for building RAG systems, which combine
retrieval systems (vector databases) with generative models.
"""

from .base import (
    BaseProvider,
    Document,
    Query,
    RAGComponent,
    RAGContext,
    RAGProvider,
    RetrievalResult,
    create_provider,
)
from .providers import ChromaProvider, InMemoryProvider

__all__ = [
    "Document",
    "Query",
    "RetrievalResult",
    "RAGProvider",
    "RAGComponent",
    "RAGContext",
    "create_provider",
    "ChromaProvider",
    "InMemoryProvider",
    "BaseProvider",
]
