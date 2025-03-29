"""Embeddings providers."""

from .fastai import FastAIEmbeddingProvider
from .local import LocalProvider
from .openai import OpenAIEmbeddingProvider

__all__ = [
    "FastAIEmbeddingProvider",
    "LocalProvider",
    "OpenAIEmbeddingProvider",
]
