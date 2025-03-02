"""Base provider abstractions for retrieval capabilities.

This module defines the base abstractions for providers that implement
various retrieval capabilities, including:

- Vector databases: For efficient similarity search and retrieval
- Document processors: For handling different document formats
- Embedding models: For converting text to vector representations

These base abstractions ensure consistent interfaces across different
provider implementations, enabling modular and extensible retrieval pipelines.
"""

from pepperpy.rag.retrieval.providers.base.base import RetrievalProvider

__all__ = [
    "RetrievalProvider",
]
