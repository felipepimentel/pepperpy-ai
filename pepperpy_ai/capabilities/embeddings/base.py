"""Base embeddings capability module."""

from abc import abstractmethod
from typing import TypeVar

from ...config.embeddings import EmbeddingsConfig
from ...embeddings.base import BaseEmbeddingsProvider
from ..base import BaseCapability

T = TypeVar("T", bound=BaseEmbeddingsProvider)


class BaseEmbeddingsCapability(BaseCapability[T]):
    """Base class for embeddings capabilities."""

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
        self.config = config
        self.provider = provider
        self._initialized = False
        self._provider_instance: T | None = None

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            list[float]: Generated embeddings.
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[list[float]]: Generated embeddings for each text.
        """
        pass
