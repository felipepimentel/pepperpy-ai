"""RAG module for PepperPy."""

from pepperpy.rag.base import (
    Document,
    Query,
    RetrievalResult,
    BaseRAGProvider,
    RAGError,
)
from pepperpy.rag.memory_optimization import (
    BaseMemoryOptimizer,
    MemoryOptimizationError,
)
from pepperpy.rag.providers import ChromaProvider

__all__ = [
    # Document types
    "Document",
    "Query",
    "RetrievalResult",
    # Memory optimization
    "BaseMemoryOptimizer",
    "MemoryOptimizationError",
    # Providers
    "BaseRAGProvider",
    "ChromaProvider",
    # Core types
    "RAGError",
]
