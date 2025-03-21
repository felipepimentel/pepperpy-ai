"""Pipeline module for PepperPy RAG.

This module provides the RAG pipeline functionality.
"""

from .pipeline import RAGPipeline
from .stages import (
    ChunkingStage,
    EmbeddingStage,
    RerankingStage,
    RetrievalStage,
)

__all__ = [
    "RAGPipeline",
    "ChunkingStage",
    "EmbeddingStage",
    "RetrievalStage",
    "RerankingStage",
]
