"""Embeddings module for PepperPy.

This module provides embeddings functionality through various providers.
"""

from pepperpy.embeddings.base import EmbeddingProvider
from pepperpy.embeddings.providers.fastai import FastAIEmbeddingProvider
from pepperpy.embeddings.providers.huggingface import HuggingFaceEmbeddingProvider
from pepperpy.embeddings.providers.local import LocalEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "FastAIEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "LocalEmbeddingProvider",
]
