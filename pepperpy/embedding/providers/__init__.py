"""Provider implementations for embedding capabilities.

This module contains implementations of various embedding providers that integrate
with external embedding services and APIs, including:

- OpenAI: Integration with OpenAI's embedding models
- Sentence Transformers: Integration with local sentence transformer models
- Hugging Face: Integration with Hugging Face's embedding models
- Azure: Integration with Azure's embedding services
- Cohere: Integration with Cohere's embedding models

These providers enable vector representation of text and documents for semantic search,
similarity comparison, and retrieval augmented generation.
"""

from pepperpy.embedding.base import BaseEmbedding, EmbeddingError
from pepperpy.embedding.providers.base import (
    BaseEmbeddingProvider,
    Embedding,
    EmbeddingProvider,
    EmbeddingResponse,
    ModelParameters,
    get_embedding_provider_class,
    list_embedding_providers,
    register_embedding_provider_class,
)
from pepperpy.embedding.providers.openai import OpenAIEmbeddingProvider
from pepperpy.embedding.registry import register_embedding

# Register providers
register_embedding("openai", OpenAIEmbeddingProvider)

__all__ = [
    "BaseEmbedding",
    "BaseEmbeddingProvider",
    "Embedding",
    "EmbeddingError",
    "EmbeddingProvider",
    "EmbeddingResponse",
    "ModelParameters",
    "OpenAIEmbeddingProvider",
    "get_embedding_provider_class",
    "list_embedding_providers",
    "register_embedding_provider_class",
]
