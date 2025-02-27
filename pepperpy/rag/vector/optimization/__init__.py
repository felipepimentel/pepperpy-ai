"""Vector index optimizations for RAG.

This module implements optimizations to improve the efficiency and performance
of vector indices in the RAG system, including:

- Memory Optimizations
  - Vector compression
  - Quantization
  - Pruning
  - Caching

- Search Optimizations
  - Approximate indexing
  - Clustering
  - Partitioning
  - Parallelization

- Quality Optimizations
  - Normalization
  - Dimensionality
  - Weighting
  - Filtering

The module provides:
- Efficient algorithms
- Optimized structures
- Performance metrics
- Adjustable configurations
"""

from typing import Dict, List, Optional, Union

from .caching import VectorCache
from .compression import PCACompressor, QuantizationCompressor, VectorCompressor
from .pruning import ThresholdPruner, TopKPruner, VectorPruner

__version__ = "0.1.0"
__all__ = [
    # Caching
    "VectorCache",
    # Compression
    "VectorCompressor",
    "PCACompressor",
    "QuantizationCompressor",
    # Pruning
    "VectorPruner",
    "ThresholdPruner",
    "TopKPruner",
]
