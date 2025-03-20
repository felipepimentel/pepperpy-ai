"""RAG (Retrieval Augmented Generation) module for PepperPy.

This module provides interfaces and implementations for RAG capabilities,
allowing efficient storage and retrieval of document embeddings.

Example:
    >>> from pepperpy.rag import RAGProvider
    >>> provider = RAGProvider.from_config({
    ...     "provider": "chroma",
    ...     "collection": "my_docs"
    ... })
    >>> await provider.add_texts(["Document 1", "Document 2"])
    >>> results = await provider.query("What's in Document 1?")
    >>> print(results[0].content)
"""

from pepperpy.rag.base import Document, Query, RAGError, RAGProvider, RetrievalResult
from pepperpy.rag.providers import (
    ChromaRAGProvider,
    LocalRAGProvider,
    OpenAIRAGProvider,
    PineconeRAGProvider,
)

__all__ = [
    # Core types
    "Document",
    "Query",
    "RAGError",
    "RAGProvider",
    "RetrievalResult",
    # Providers
    "ChromaRAGProvider",
    "LocalRAGProvider",
    "OpenAIRAGProvider",
    "PineconeRAGProvider",
]
