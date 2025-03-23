"""RAG provider implementations for PepperPy.

This module provides various RAG (Retrieval Augmented Generation) provider
implementations, each with its own characteristics and trade-offs:

- AnnoyRAGProvider: Default lightweight provider using Annoy for vector similarity search
- ChromaRAGProvider: Robust provider using ChromaDB for vector storage
- FAISSRAGProvider: High-performance provider using FAISS for vector search
- SQLiteRAGProvider: Simple provider using SQLite for vector storage
- LocalRAGProvider: Basic provider using local file storage
- OpenAIRAGProvider: Provider using OpenAI's vector search capabilities
- PineconeRAGProvider: Provider using Pinecone for vector search
"""

from .annoy import AnnoyRAGProvider
from .chroma import ChromaRAGProvider
from .local import LocalRAGProvider

__all__ = [
    "AnnoyRAGProvider",  # Default provider
    "ChromaRAGProvider",
    "LocalRAGProvider",
]

# Optional providers that require additional dependencies
try:
    from .faiss import FAISSRAGProvider

    __all__.append("FAISSRAGProvider")
except ImportError:
    pass

try:
    from .sqlite import SQLiteRAGProvider

    __all__.append("SQLiteRAGProvider")
except ImportError:
    pass

try:
    from .openai import OpenAIRAGProvider

    __all__.append("OpenAIRAGProvider")
except ImportError:
    pass

try:
    from .pinecone import PineconeRAGProvider

    __all__.append("PineconeRAGProvider")
except ImportError:
    pass

try:
    from .supabase import SupabaseRAGProvider

    __all__.append("SupabaseRAGProvider")
except ImportError:
    pass

# Set default provider
DEFAULT_PROVIDER = AnnoyRAGProvider
