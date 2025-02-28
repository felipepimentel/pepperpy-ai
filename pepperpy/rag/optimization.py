"""RAG optimization components.

This module re-exports the optimization components from the processors subpackage.
"""

from .processors.optimization import (
    # Compression
    DimensionalityReducer,
    # Pruning
    DiversityPruner,
    QualityPruner,
    QuantizationCompressor,
    RedundancyPruner,
    VectorCompressor,
    VectorPruner,
)

__all__ = [
    # Compression
    "DimensionalityReducer",
    "VectorCompressor",
    "QuantizationCompressor",
    # Pruning
    "RedundancyPruner",
    "QualityPruner",
    "DiversityPruner",
    "VectorPruner",
] 