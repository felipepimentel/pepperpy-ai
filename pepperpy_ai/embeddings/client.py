"""Embeddings client module."""

from typing import Any

from ..config.embeddings import EmbeddingsConfig
from .base import BaseEmbeddingsProvider
from .providers.sentence_transformers import SentenceTransformersProvider
from .providers.simple import SimpleEmbeddingsProvider


class EmbeddingsClient:
    """Embeddings client class."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize embeddings client.

        Args:
            config: Embeddings configuration.
        """
        self.config = config
        self._provider: BaseEmbeddingsProvider | None = None

    @property
    def is_initialized(self) -> bool:
        """Return whether the client is initialized."""
        return self._provider is not None and self._provider.is_initialized

    async def initialize(self) -> None:
        """Initialize client."""
        if self.is_initialized:
            return

        provider_type = self.config.get("provider_type", "simple")
        model = self.config.get("model", "all-MiniLM-L6-v2")
        api_key = self.config.get("api_key", "")

        if not api_key:
            raise ValueError("API key is required")

        # Create embeddings config with required fields
        embeddings_config: EmbeddingsConfig = {
            "name": provider_type,
            "version": "1.0.0",
            "model": model,
            "api_key": api_key,
            "enabled": self.config.get("enabled", True),
            "normalize": self.config.get("normalize", True),
            "batch_size": self.config.get("batch_size", 32),
            "device": self.config.get("device", "cpu"),
        }

        if provider_type == "simple":
            self._provider = SimpleEmbeddingsProvider(embeddings_config)
        elif provider_type == "sentence_transformers":
            self._provider = SentenceTransformersProvider(embeddings_config)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        await self._provider.initialize()

    async def cleanup(self) -> None:
        """Cleanup client."""
        if self._provider is not None:
            await self._provider.cleanup()
            self._provider = None

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            List of embeddings.

        Raises:
            ValueError: If client is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Client not initialized")

        assert self._provider is not None
        return await self._provider.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            List of embeddings.

        Raises:
            ValueError: If client is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Client not initialized")

        assert self._provider is not None
        return await self._provider.embed_batch(texts)
