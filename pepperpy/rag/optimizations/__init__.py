"""RAG Optimizations Module

This module provides optimization techniques for Retrieval-Augmented Generation (RAG) systems:

- Caching:
  - Efficient storage and retrieval of embeddings and query results
  - Reduces redundant computation and API calls
  - Improves response time for repeated or similar queries

- Compression:
  - Techniques to reduce the size of vector representations
  - Dimensionality reduction for more efficient storage
  - Quantization to reduce memory footprint
  - Preserves semantic similarity while reducing resource usage

- Pruning:
  - Methods to remove redundant or low-quality vectors
  - Diversity-based filtering to reduce information overlap
  - Quality-based filtering to maintain high relevance
  - Redundancy elimination to optimize vector stores

These optimizations help improve performance, reduce resource usage, enhance
retrieval quality, and lower operational costs of RAG systems.
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
