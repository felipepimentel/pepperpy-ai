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

from pepperpy.rag.document import Document
from pepperpy.rag.memory_optimization import (
    DocumentChunk,
    StreamingProcessor,
    get_memory_usage,
    optimize_memory_usage,
    process_document_streaming,
    stream_document,
)
from pepperpy.rag.provider import RAGError, RAGProvider
from pepperpy.rag.providers import (
    ChromaRAGProvider,
    LocalRAGProvider,
    OpenAIRAGProvider,
    PineconeRAGProvider,
)
from pepperpy.rag.query import Query
from pepperpy.rag.result import RetrievalResult

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
    # Memory optimization
    "DocumentChunk",
    "StreamingProcessor",
    "get_memory_usage",
    "optimize_memory_usage",
    "process_document_streaming",
    "stream_document",
]
