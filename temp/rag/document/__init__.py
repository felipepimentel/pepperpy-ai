"""Document processing module for RAG.

This module provides functionality for document processing in RAG,
including document representation, loading, and processing.
"""

from pepperpy.rag.document.core import (
    Document,
    DocumentChunk,
    DocumentLoader,
    DocumentProcessor,
    DocumentStore,
    Metadata,
)

__all__ = [
    "Document",
    "DocumentChunk",
    "DocumentLoader",
    "DocumentProcessor",
    "DocumentStore",
    "Metadata",
]
