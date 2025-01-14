"""Simple RAG capability module."""

from collections.abc import Sequence
from typing import Any

from pepperpy.capabilities.base import BaseCapability
from pepperpy.capabilities.rag.document import Document
from pepperpy.embeddings.providers.sentence_transformers import (
    SentenceTransformersProvider,
)
from pepperpy.exceptions import DependencyError
from pepperpy.types import CapabilityConfig


class SimpleRAGCapability(BaseCapability[CapabilityConfig]):
    """Simple RAG capability."""

    def __init__(self, config: CapabilityConfig) -> None:
        """Initialize simple RAG capability.

        Args:
            config: Capability configuration.
        """
        super().__init__(config)
        self._embeddings_provider: SentenceTransformersProvider | None = None

    async def initialize(self) -> None:
        """Initialize capability.

        Raises:
            DependencyError: If required dependencies are not installed.
        """
        if not self.is_initialized:
            self._embeddings_provider = SentenceTransformersProvider(self.config)
            await self._embeddings_provider.initialize()
            await super().initialize()

    async def cleanup(self) -> None:
        """Clean up capability."""
        if self._embeddings_provider:
            await self._embeddings_provider.cleanup()
            self._embeddings_provider = None
        await super().cleanup()

    async def _embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text.

        Args:
            text: Text to embed.
            **kwargs: Additional arguments.

        Returns:
            list[float]: Embedding.

        Raises:
            DependencyError: If embeddings provider is not initialized.
        """
        if not self._embeddings_provider:
            raise DependencyError(
                "Embeddings provider not initialized",
                package="sentence-transformers",
            )
        return await self._embeddings_provider.embed_text(text, **kwargs)

    async def _embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Embed texts.

        Args:
            texts: List of texts to embed.
            **kwargs: Additional arguments.

        Returns:
            list[list[float]]: List of embeddings.

        Raises:
            DependencyError: If embeddings provider is not initialized.
        """
        if not self._embeddings_provider:
            raise DependencyError(
                "Embeddings provider not initialized",
                package="sentence-transformers",
            )
        return await self._embeddings_provider.embed_texts(texts, **kwargs)
