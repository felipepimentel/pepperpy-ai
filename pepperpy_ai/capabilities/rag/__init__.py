"""RAG (Retrieval Augmented Generation) capabilities."""

from .base import BaseRAG, Document, RAGConfig

__all__ = [
    "BaseRAG",
    "Document",
    "RAGConfig",
]

# Optional implementations
try:
    from .simple import SimpleRAG, SimpleRAGConfig
    from .strategies import (
        BaseRAGStrategy,
        RAGStrategyConfig,
        SemanticRAGConfig,
        SemanticRAGStrategy,
    )
    __all__.extend([
        "SimpleRAG",
        "SimpleRAGConfig",
        "BaseRAGStrategy",
        "RAGStrategyConfig",
        "SemanticRAGConfig",
        "SemanticRAGStrategy",
    ])
except ImportError:
    pass 