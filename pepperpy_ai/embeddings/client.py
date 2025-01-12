"""Embeddings client module."""

from typing import List, Optional, Type

from .base import EmbeddingsConfig
from .providers.base import BaseEmbeddingsProvider
from ..exceptions import EmbeddingsError


class EmbeddingsClient:
    """Client for embeddings providers."""

    def __init__(
        self,
        provider: Type[BaseEmbeddingsProvider],
        config: Optional[EmbeddingsConfig] = None,
    ) -> None:
        """Initialize client.

        Args:
            provider: Provider class to use
            config: Optional provider configuration
        """
        self.config = config or EmbeddingsConfig()
        self._provider_class = provider
        self._provider_instance: Optional[BaseEmbeddingsProvider] = None
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize client."""
        if not self._provider_instance:
            self._provider_instance = self._provider_class(self.config)
            await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        if self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None
            self._initialized = False

    async def embed(self, text: str) -> List[float]:
        """Get embeddings for text.

        Args:
            text: Text to get embeddings for

        Returns:
            List of embeddings

        Raises:
            EmbeddingsError: If client is not initialized
        """
        if not self.is_initialized or not self._provider_instance:
            raise EmbeddingsError("Client not initialized")

        return await self._provider_instance.embed(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts.

        Args:
            texts: List of texts to get embeddings for

        Returns:
            List of embeddings lists

        Raises:
            EmbeddingsError: If client is not initialized
        """
        if not self.is_initialized or not self._provider_instance:
            raise EmbeddingsError("Client not initialized")

        return await self._provider_instance.embed_batch(texts)
