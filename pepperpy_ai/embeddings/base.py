"""Base embeddings provider module."""

from abc import ABC, abstractmethod

from ..config.embeddings import EmbeddingsConfig
from .types import BatchEmbeddingResult, EmbeddingResult


class BaseEmbeddingsProvider(ABC):
    """Base class for embeddings providers."""

    def __init__(self, config: EmbeddingsConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration.
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup provider."""
        raise NotImplementedError

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Embed a single text.

        Args:
            text: The text to embed.

        Returns:
            A list of embedding values.

        Raises:
            ProviderError: If the provider is not initialized or if an error occurs.
        """
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> BatchEmbeddingResult:
        """Embed a list of texts.

        Args:
            texts: The texts to embed.

        Returns:
            A list of embedding value lists.

        Raises:
            ProviderError: If the provider is not initialized or if an error occurs.
        """
        raise NotImplementedError
