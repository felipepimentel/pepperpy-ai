"""RAG Processing Components.

This module provides specialized processors for RAG (Retrieval Augmented Generation) systems:

- Preprocessing
  - Document chunking
  - Content preparation
  - Text segmentation
  - Metadata extraction

- Optimization
  - Vector compression
  - Dimensionality reduction
  - Pruning techniques
  - Quality filtering

The module provides:
- Standardized interfaces
- Flexible configuration
- Modular pipeline
- Extensibility
"""

from pepperpy.rag.processors.optimization import (
    DimensionalityReducer,
    DiversityPruner,
    QualityPruner,
    QuantizationCompressor,
    RedundancyPruner,
    VectorCompressor,
    VectorPruner,
)
from pepperpy.rag.processors.preprocessing import (
    Augmenter,
    Chunker,
    ContextAugmenter,
    ParagraphChunker,
    QueryAugmenter,
    ResultAugmenter,
    SentenceChunker,
    TextChunker,
    TokenChunker,
)

__version__ = "0.1.0"
__all__ = [
    # Preprocessing
    "Chunker",
    "TextChunker",
    "TokenChunker",
    "SentenceChunker",
    "ParagraphChunker",
    "Augmenter",
    "QueryAugmenter",
    "ResultAugmenter",
    "ContextAugmenter",
    # Optimization
    "VectorCompressor",
    "DimensionalityReducer",
    "QuantizationCompressor",
    "VectorPruner",
    "QualityPruner",
    "RedundancyPruner",
    "DiversityPruner",
]
