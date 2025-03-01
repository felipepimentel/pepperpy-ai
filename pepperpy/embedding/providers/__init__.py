"""Embedding providers module.

This module provides implementations of various embedding providers
for converting text into vector embeddings.

DEPRECATED: This module has been moved to pepperpy.providers.embedding.
Please update your imports. This compatibility stub will be removed in a future version.
"""

import warnings

warnings.warn(
    "The module pepperpy.embedding.providers has been moved to pepperpy.providers.embedding. "
    "Please update your imports. This compatibility stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from the new location
from pepperpy.providers.embedding.base import EmbeddingError, EmbeddingProvider
from pepperpy.providers.embedding.openai import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingError",
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
