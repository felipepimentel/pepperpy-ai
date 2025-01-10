"""Embedding client implementation."""

from .base import EmbeddingProvider


class EmbeddingClient:
    """Embedding client implementation."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        """Initialize client."""
        self._provider = provider
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize client."""
        if not self._initialized:
            await self._provider.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        if self._initialized:
            await self._provider.cleanup()
            self._initialized = False

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        return await self._provider.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        return await self._provider.embed_batch(texts)
