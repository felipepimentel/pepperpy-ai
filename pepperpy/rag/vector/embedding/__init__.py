"""Embedding module for RAG (DEPRECATED)

This module is deprecated, use pepperpy.rag.embedders instead.
This module will be removed in version 1.0.0.
"""

import warnings
from typing import Any, Dict

# Import from new location for backward compatibility
from ...embedders import TextEmbedder as EmbeddingModel

# Configuration type for backward compatibility
EmbeddingConfig = Dict[str, Any]

# Show deprecation warning
warnings.warn(
    "The 'pepperpy.rag.vector.embedding' module is deprecated and will be removed in version 1.0.0. "
    "Please use 'pepperpy.rag.embedders' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["EmbeddingModel", "EmbeddingConfig"]
