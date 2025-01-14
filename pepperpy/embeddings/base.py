"""Base embeddings provider module."""

from abc import ABC, abstractmethod
from typing import Any

from pepperpy.capabilities.base import BaseCapability
from pepperpy.types import CapabilityConfig


class BaseEmbeddingsProvider(BaseCapability[CapabilityConfig], ABC):
    """Base embeddings provider."""

    @abstractmethod
    async def _embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text.

        Args:
            text: Text to embed.
            **kwargs: Additional arguments.

        Returns:
            list[float]: Embedding.
        """
        raise NotImplementedError

    @abstractmethod
    async def _embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Embed texts.

        Args:
            texts: List of texts to embed.
            **kwargs: Additional arguments.

        Returns:
            list[list[float]]: List of embeddings.
        """
        raise NotImplementedError

    async def embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text.

        Args:
            text: Text to embed.
            **kwargs: Additional arguments.

        Returns:
            list[float]: Embedding.
        """
        if not self.is_initialized:
            await self.initialize()
        return await self._embed_text(text, **kwargs)

    async def embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Embed texts.

        Args:
            texts: List of texts to embed.
            **kwargs: Additional arguments.

        Returns:
            list[list[float]]: List of embeddings.
        """
        if not self.is_initialized:
            await self.initialize()
        return await self._embed_texts(texts, **kwargs)
