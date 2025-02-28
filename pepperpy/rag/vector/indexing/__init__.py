"""Indexing module for RAG (DEPRECATED)

This module is deprecated, use pepperpy.rag.indexers instead.
This module will be removed in version 1.0.0.
"""

import warnings
from typing import Any, Dict

# Import from new location for backward compatibility
from ...indexers import VectorIndexer as VectorIndex

# Configuration type for backward compatibility
IndexConfig = Dict[str, Any]

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.rag.vector.indexing' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.rag.indexers' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["VectorIndex", "IndexConfig"]
