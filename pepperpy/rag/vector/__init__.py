"""Vector embedding and indexing module for RAG (DEPRECATED)

This module is deprecated, use top-level RAG components instead.

The functionality has been moved to the following locations:
- pepperpy/rag/vector/embedding/embedders.py → pepperpy/rag/embedders.py
- pepperpy/rag/vector/indexing/indexers.py → pepperpy/rag/indexers.py
- pepperpy/rag/vector/optimization/ → pepperpy/rag/optimizations/

This module will be removed after a transition period (scheduled for removal in v1.0.0).
"""

import warnings
from typing import Dict, List, Optional, Union

# Import from new locations for backward compatibility
from ..embedders import TextEmbedder as EmbeddingModel
from ..indexers import VectorIndexer as VectorIndex

# Configuration types for backward compatibility
EmbeddingConfig = Dict[str, any]
IndexConfig = Dict[str, any]
VectorOptimizer = Dict[str, any]

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.rag.vector' module is deprecated and will be removed in version 1.0.0. "
    "Please use the top-level RAG components instead (pepperpy.rag.embedders, "
    "pepperpy.rag.indexers, pepperpy.rag.optimizations).",
    DeprecationWarning,
    stacklevel=2,
)

__version__ = "0.1.0"
__all__ = [
    "EmbeddingModel",
    "EmbeddingConfig",
    "VectorIndex",
    "IndexConfig",
    "VectorOptimizer",
]
