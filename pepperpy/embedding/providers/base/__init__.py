"""Base module for embedding providers.

This module provides the base classes and interfaces for embedding providers.
"""

from pepperpy.embedding.providers.base.base import BaseEmbeddingProvider
from pepperpy.embedding.providers.base.registry import (
    get_embedding_provider_class,
    register_embedding_provider_class,
)
from pepperpy.embedding.providers.base.types import (
    Embedding,
    EmbeddingProvider,
    EmbeddingResponse,
    ModelParameters,
)

__all__ = [
    "BaseEmbeddingProvider",
    "Embedding",
    "EmbeddingProvider",
    "EmbeddingResponse",
    "ModelParameters",
    "get_embedding_provider_class",
    "register_embedding_provider_class",
]
