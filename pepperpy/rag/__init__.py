"""RAG module for PepperPy."""

from pepperpy.rag.base import (
    Document,
    Query,
    BaseProvider,
    RAGContext,
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
    # Memory optimization
    "BaseMemoryOptimizer",
    "MemoryOptimizationError",
    # Providers
    "BaseProvider",
    "ChromaProvider",
    # Context
    "RAGContext",
]
