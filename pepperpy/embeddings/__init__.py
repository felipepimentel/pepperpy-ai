"""Embeddings module for PepperPy.

This module provides embeddings functionality through various providers.
"""

from pepperpy.embeddings.base import (
    EmbeddingProvider,
    EmbeddingsProvider,
    create_provider,
)
from pepperpy.embeddings.providers.fastai import FastAIEmbeddingProvider
from pepperpy.embeddings.providers.huggingface import HuggingFaceEmbeddingProvider
from pepperpy.embeddings.providers.local import LocalProvider

__all__ = [
    "EmbeddingProvider",
    "EmbeddingsProvider",
    "create_provider",
    "FastAIEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "LocalProvider",
]
