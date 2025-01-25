"""
Embedding provider implementations for Pepperpy.
"""

from pepperpy.providers.embedding.base import EmbeddingProvider
from pepperpy.providers.embedding.sentence_transformers import SentenceTransformersProvider

__all__ = ["EmbeddingProvider", "SentenceTransformersProvider"] 