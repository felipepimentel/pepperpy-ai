"""
RAG Optimizations Module

This module provides optimization techniques for RAG systems, including:
- Caching: Efficient storage and retrieval of embeddings and query results
- Compression: Techniques to reduce the size of vector representations
- Pruning: Methods to remove redundant or low-quality vectors

These optimizations help improve performance, reduce resource usage, and enhance
the overall efficiency of RAG systems.
"""

from .caching import (
    EmbeddingCache,
    QueryCache,
    ResultCache,
)
from .compression import (
    DimensionalityReducer,
    QuantizationCompressor,
    VectorCompressor,
)
from .pruning import (
    DiversityPruner,
    QualityPruner,
    RedundancyPruner,
)

__all__ = [
    # Caching
    "EmbeddingCache",
    "QueryCache",
    "ResultCache",
    # Compression
    "DimensionalityReducer",
    "VectorCompressor",
    "QuantizationCompressor",
    # Pruning
    "RedundancyPruner",
    "QualityPruner",
    "DiversityPruner",
]
