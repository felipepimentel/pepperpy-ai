"""Base embeddings module."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from ..config.embeddings import EmbeddingsConfig
from ..providers.base import BaseProvider


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embeddings: list[float]
    metadata: dict[str, Any]


class BaseEmbeddingsProvider(BaseProvider[EmbeddingsConfig]):
    """Base class for embeddings providers."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
        """
        super().__init__(config, config.api_key or "")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized.

        Raises:
            RuntimeError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            EmbeddingResult: Generated embeddings.
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[EmbeddingResult]: Generated embeddings for each text.
        """
        pass
