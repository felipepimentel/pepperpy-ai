"""Embedding model provider implementation.

This module implements the embedding model provider for RAG capabilities.
"""

from typing import Any, Dict

from pepperpy.rag.providers.base.base import RagProvider
from pepperpy.rag.providers.base.types import ProviderType


class EmbeddingModelProvider(RagProvider):
    """Embedding model provider implementation.

    This provider integrates with embedding models to convert text
    to vector representations for semantic search.
    """

    async def initialize(self) -> None:
        """Initialize the embedding model provider."""

    async def cleanup(self) -> None:
        """Clean up the embedding model provider."""

    @property
    def provider_info(self) -> Dict[str, Any]:
        """Get information about the provider.

        Returns:
            A dictionary containing information about the provider

        """
        return {
            "provider_type": ProviderType.EMBEDDING_MODEL,
            "provider_id": "embedding_model",
            "description": "Embedding model provider for RAG",
        }
