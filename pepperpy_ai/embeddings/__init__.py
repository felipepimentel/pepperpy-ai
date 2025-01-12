"""Embeddings module exports."""

from .base import EmbeddingsConfig
from .client import EmbeddingsClient
from .providers import SimpleEmbeddingsProvider

__all__ = ["EmbeddingsClient", "EmbeddingsConfig", "SimpleEmbeddingsProvider"]
