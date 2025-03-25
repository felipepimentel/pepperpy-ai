"""Embeddings module for PepperPy.

This module provides text-to-vector embedding capabilities for the PepperPy framework.
"""

from .base import EmbeddingProvider
from .errors import EmbeddingError

__all__ = [
    "EmbeddingProvider",
    "EmbeddingError",
]
