"""Simple embeddings capability implementation."""

from typing import TypeVar

from ...config.embeddings import EmbeddingsConfig
from ...embeddings.base import BaseEmbeddingsProvider
from .base import BaseEmbeddingsCapability

T = TypeVar("T", bound=BaseEmbeddingsProvider)


class SimpleEmbeddingsCapability(BaseEmbeddingsCapability[T]):
    """A simple embeddings capability implementation.

    This implementation provides basic embeddings functionality using
    a configurable provider.
    """

    def __init__(
        self,
        config: EmbeddingsConfig,
        provider: type[T],
    ) -> None:
        """Initialize embeddings capability.

        Args:
            config: Capability configuration.
            provider: Provider class to use.
        """
        super().__init__(config, provider)

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            list[float]: Generated embeddings.
        """
        self._ensure_initialized()
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")
        result = await self._provider_instance.embed(text)
        return result.embeddings

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[list[float]]: Generated embeddings for each text.
        """
        self._ensure_initialized()
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")
        results = await self._provider_instance.embed_batch(texts)
        return [result.embeddings for result in results]
