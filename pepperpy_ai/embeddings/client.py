"""Embeddings client module."""

from typing import Generic, TypeVar

from ..config.embeddings import EmbeddingsConfig
from .base import BaseEmbeddingsProvider

T = TypeVar("T", bound=BaseEmbeddingsProvider)


class EmbeddingsClient(Generic[T]):
    """Client for embeddings generation."""

    def __init__(
        self,
        provider: type[T],
        name: str,
        version: str,
        model: str,
        enabled: bool = True,
        normalize: bool = True,
        batch_size: int = 32,
        api_key: str | None = None,
    ) -> None:
        """Initialize client.

        Args:
            provider: Provider class to use.
            name: Client name.
            version: Client version.
            model: Model name or path.
            enabled: Whether embeddings are enabled.
            normalize: Whether to normalize embeddings.
            batch_size: Batch size for embedding generation.
            api_key: API key for authentication.
        """
        self.config = EmbeddingsConfig(
            name=name,
            version=version,
            model=model,
            enabled=enabled,
            normalize=normalize,
            batch_size=batch_size,
            api_key=api_key,
        )
        self.provider = provider
        self._provider_instance: T | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize client resources."""
        if not self._initialized:
            if not self._provider_instance:
                self._provider_instance = self.provider(self.config)
                await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up client resources."""
        if self._initialized and self._provider_instance:
            await self._provider_instance.cleanup()
            self._initialized = False

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            list[float]: Generated embeddings.
        """
        if not self._initialized:
            await self.initialize()
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
        if not self._initialized:
            await self.initialize()
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")
        results = await self._provider_instance.embed_batch(texts)
        return [result.embeddings for result in results]
