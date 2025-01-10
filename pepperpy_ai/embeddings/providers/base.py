"""Base embedding provider implementation."""

from abc import ABC, abstractmethod

from ..base import EmbeddingProvider


class BaseEmbeddingProvider(EmbeddingProvider, ABC):
    """Base embedding provider implementation."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        pass
