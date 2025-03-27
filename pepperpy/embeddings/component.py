"""Embeddings component module."""

from typing import List, Optional, Union

from pepperpy.core.base import BaseComponent
from pepperpy.core.config import Config
from pepperpy.embeddings.base import EmbeddingProvider, create_provider


class EmbeddingComponent(BaseComponent):
    """Embeddings component for text embeddings."""

    def __init__(self, config: Config) -> None:
        """Initialize embeddings component.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self._provider: Optional[EmbeddingProvider] = None

    async def _initialize(self) -> None:
        """Initialize the embeddings provider."""
        provider_type = self.config.get("embeddings.provider", "openai")
        provider_config = self.config.get("embeddings.config", {})
        self._provider = create_provider(provider_type, **provider_config)
        await self._provider.initialize()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._provider:
            await self._provider.cleanup()

    async def embed_single_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text.

        Args:
            text: Text to embed

        Returns:
            Text embeddings as a list of float values
        """
        if not self._provider:
            await self._initialize()

        # Ensure provider is initialized
        assert self._provider is not None

        # Use embed_query which returns List[float] directly
        return await self._provider.embed_query(text)

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for text(s).

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._provider:
            await self._initialize()

        # Ensure provider is initialized
        assert self._provider is not None

        # Forward directly to provider's implementation
        return await self._provider.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        This is an alias for embed_text with a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        return await self.embed_text(texts)
