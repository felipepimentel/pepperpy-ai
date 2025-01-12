"""Base embeddings provider module."""

from abc import ABC, abstractmethod
from typing import List

from ..base import EmbeddingsConfig


class BaseEmbeddingsProvider(ABC):
    """Base class for embeddings providers."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        raise NotImplementedError

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Get embeddings for text.

        Args:
            text: Text to get embeddings for

        Returns:
            List of embeddings
        """
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts.

        Args:
            texts: List of texts to get embeddings for

        Returns:
            List of embeddings lists
        """
        raise NotImplementedError
