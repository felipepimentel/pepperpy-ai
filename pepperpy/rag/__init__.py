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

# Definir uma classe RAGContext simples para compatibilidade
class RAGContext:
    """Context for RAG operations."""
    
    def __init__(self, provider=None, config=None):
        """Initialize the RAG context.
        
        Args:
            provider: Optional RAG provider.
            config: Optional configuration.
        """
        self.provider = provider
        self.config = config or {}

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
    # Context
    "RAGContext",
]
