"""Public Interface for embeddings

This module provides a stable public interface for the embeddings functionality.
It exposes the core embedding abstractions and implementations that are considered
part of the public API.

Classes:
    Embedder: Base class for text embedding
    TextEmbedder: Embedder for raw text
    DocumentEmbedder: Embedder for documents
    SentenceEmbedder: Embedder for sentences
    EmbeddingProvider: Base provider for embedding services
    CachedEmbedder: Embedder with caching support
    ModelRegistry: Registry for embedding models
    ProviderFactory: Factory for embedding providers
    EmbeddingProcessor: Utilities for processing embeddings
"""

from typing import Any, Dict, List, Optional, Union

# Caching support
from pepperpy.caching.base import Cache
from pepperpy.caching.vector import VectorCache

# Core embedding functionality
from pepperpy.embedding.rag import (
    DocumentEmbedder,
    Embedder,
    SentenceEmbedder,
    TextEmbedder,
)

# Model classes
from pepperpy.interfaces.embeddings.models import (
    EmbeddingModel,
    HuggingFaceEmbeddingModel,
    ModelRegistry,
    OpenAIEmbeddingModel,
    SentenceTransformerModel,
)

# Provider base classes
from pepperpy.interfaces.embeddings.providers import (
    AzureEmbeddingProvider,
    CohereEmbeddingProvider,
    EmbeddingProvider,
    HuggingFaceEmbeddingProvider,
    OpenAIEmbeddingProvider,
    ProviderFactory,
)

# Utility functions and classes
from pepperpy.interfaces.embeddings.utils import (
    EmbeddingProcessor,
    average_embeddings,
    cosine_similarity,
    dot_product,
    embedding_statistics,
    euclidean_distance,
    normalize_embeddings,
)


class CachedEmbedder:
    """Embedder with integrated caching support.

    This class wraps any embedder implementation with a vector cache
    to improve performance and reduce API calls.
    """

    def __init__(
        self,
        embedder: Embedder,
        cache: Optional[VectorCache] = None,
        cache_ttl: int = 3600,  # 1 hour in seconds
    ):
        """Initialize cached embedder.

        Args:
            embedder: Base embedder implementation
            cache: Optional vector cache (creates a new one if None)
            cache_ttl: Cache TTL in seconds
        """
        self.embedder = embedder
        self.cache = cache or VectorCache()
        self.cache_ttl = cache_ttl

    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Convert text into vector embeddings with caching.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embedding vectors
        """
        # Handle single text vs list of texts
        texts = [text] if isinstance(text, str) else text
        results = []

        # Check cache for each text
        uncached_texts = []
        uncached_indices = []

        for i, t in enumerate(texts):
            cache_key = f"embed:{hash(t)}"
            if await self.cache.contains(cache_key):
                # Cache hit
                embedding = await self.cache.get(cache_key)
                results.append(embedding)
            else:
                # Cache miss
                uncached_texts.append(t)
                uncached_indices.append(i)

        # Get embeddings for uncached texts
        if uncached_texts:
            new_embeddings = await self.embedder.embed(uncached_texts)

            # Store in cache and add to results
            for i, embedding in zip(uncached_indices, new_embeddings):
                cache_key = f"embed:{hash(texts[i])}"
                await self.cache.set(cache_key, embedding, ttl=self.cache_ttl)
                results.append(embedding)

        # Return embeddings
        return results


# Export public API
__all__ = [
    # Core embedding classes
    "Embedder",
    "TextEmbedder",
    "DocumentEmbedder",
    "SentenceEmbedder",
    # Provider classes
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "AzureEmbeddingProvider",
    "CohereEmbeddingProvider",
    # Model classes
    "EmbeddingModel",
    "OpenAIEmbeddingModel",
    "HuggingFaceEmbeddingModel",
    "SentenceTransformerModel",
    # Utility classes and functions
    "CachedEmbedder",
    "Cache",
    "VectorCache",
    "ModelRegistry",
    "ProviderFactory",
    "EmbeddingProcessor",
    # Utility functions
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
    "normalize_embeddings",
    "average_embeddings",
    "embedding_statistics",
]
