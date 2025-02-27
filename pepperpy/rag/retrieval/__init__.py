"""RAG retrieval package.

This package provides functionality for retrieving relevant documents and
content from indexed collections based on queries.
"""

from .retrievers import (
    Retriever,
    VectorRetriever,
    TextRetriever,
    HybridRetriever,
)

__all__ = [
    # Base class
    "Retriever",
    # Specific retrievers
    "VectorRetriever",
    "TextRetriever",
    "HybridRetriever",
]