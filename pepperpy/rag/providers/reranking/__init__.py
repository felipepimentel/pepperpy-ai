"""Reranking providers module.

This module provides functionality for reranking documents based on relevance.
"""

from pepperpy.rag.providers.reranking.base import BaseRerankingProvider
from pepperpy.rag.providers.reranking.mock import MockRerankingProvider

# Try to import torch-dependent providers
try:
    from pepperpy.rag.providers.reranking.cross_encoder import CrossEncoderProvider

    _has_torch = True
except ImportError:
    _has_torch = False

__all__ = [
    "BaseRerankingProvider",
    "MockRerankingProvider",
]

# Add torch-dependent providers to __all__ if available
if _has_torch:
    __all__.append("CrossEncoderProvider")
