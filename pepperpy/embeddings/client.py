"""Embeddings client module."""

from typing import Any

from pepperpy.embeddings.base import BaseEmbeddingsProvider
from pepperpy.embeddings.providers.sentence_transformers import (
    SentenceTransformersProvider,
)
from pepperpy.exceptions import DependencyError
from pepperpy.types import CapabilityConfig


class EmbeddingsClient:
    """Embeddings client."""

    def __init__(self, config: CapabilityConfig) -> None:
        """Initialize embeddings client.

        Args:
            config: Client configuration.
        """
        self._config = config
        self._provider: BaseEmbeddingsProvider | None = None

    @property
    def provider(self) -> BaseEmbeddingsProvider:
        """Get embeddings provider.

        Returns:
            BaseEmbeddingsProvider: Embeddings provider.

        Raises:
            DependencyError: If provider is not initialized.
        """
        if not self._provider:
            raise DependencyError(
                "Provider not initialized", package="sentence-transformers"
            )
        return self._provider

    async def initialize(self) -> None:
        """Initialize client.

        Raises:
            DependencyError: If provider is not initialized.
        """
        if not self._provider:
            self._provider = SentenceTransformersProvider(self._config)
            await self._provider.initialize()

    async def cleanup(self) -> None:
        """Clean up client."""
        if self._provider:
            await self._provider.cleanup()
            self._provider = None

    async def embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text.

        Args:
            text: Text to embed.
            **kwargs: Additional arguments.

        Returns:
            list[float]: Embedding.

        Raises:
            DependencyError: If provider is not initialized.
        """
        return await self.provider.embed_text(text, **kwargs)

    async def embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Embed texts.

        Args:
            texts: List of texts to embed.
            **kwargs: Additional arguments.

        Returns:
            list[list[float]]: List of embeddings.

        Raises:
            DependencyError: If provider is not initialized.
        """
        return await self.provider.embed_texts(texts, **kwargs)
