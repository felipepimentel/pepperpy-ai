"""Embeddings module for Pepperpy."""

from .base import EmbeddingModel
from .openai import OpenAIEmbeddingModel


__all__ = [
    "EmbeddingModel",
    "OpenAIEmbeddingModel",
] 