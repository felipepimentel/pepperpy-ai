"""Embeddings component module."""

from typing import List, Optional

from pepperpy.core.base import BaseComponent
from pepperpy.core.config import Config
from pepperpy.embeddings.base import EmbeddingProvider


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
        self._provider = self.config.load_embedding_provider()
        await self._provider.initialize()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._provider:
            await self._provider.cleanup()

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed

        Returns:
            Text embeddings
        """
        if not self._provider:
            await self.initialize()
        return await self._provider.embed_text(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of text embeddings
        """
        if not self._provider:
            await self.initialize()
        return await self._provider.embed_texts(texts)
