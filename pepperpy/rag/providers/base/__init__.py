"""Base provider abstractions for RAG capabilities.

This module defines the base abstractions for providers that implement
various RAG capabilities, including:

- Vector databases: For efficient similarity search and retrieval
- Document processors: For handling different document formats
- Embedding models: For converting text to vector representations
- Knowledge bases: For structured information retrieval
- Search engines: For web and enterprise search integration

These base abstractions ensure consistent interfaces across different
provider implementations, enabling modular and extensible RAG pipelines.
"""

from pepperpy.rag.providers.base.base import RagProvider

__all__ = [
    "RagProvider",
]
