"""RAG Processing Components.

This module provides specialized components for processing data in RAG (Retrieval Augmented Generation) systems:
- Preprocessing tools for document chunking and content preparation
- Optimization techniques for vector representations and embeddings

These components help improve the quality and efficiency of RAG systems by properly
preparing content for indexing and retrieval.
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
