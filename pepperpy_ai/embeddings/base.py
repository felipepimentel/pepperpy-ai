"""Base embeddings provider module."""

from abc import abstractmethod
from typing import TypedDict

from ..providers.base import BaseProvider
from .config import EmbeddingsConfig
from .types import EmbeddingResult


class EmbeddingKwargs(TypedDict, total=False):
    """Embedding keyword arguments."""

    batch_size: int
    normalize: bool
    device: str
    model: str


class BaseEmbeddingsProvider(BaseProvider):
    """Base class for embeddings providers."""

    def __init__(self, config: EmbeddingsConfig, api_key: str) -> None:
        """Initialize the embeddings provider.

        Args:
            config: The embeddings configuration.
            api_key: The API key for the provider.
        """
        super().__init__(config, api_key)

    @abstractmethod
    async def embed(
        self, texts: list[str], **kwargs: EmbeddingKwargs
    ) -> list[EmbeddingResult]:
        """Embed a list of texts.

        Args:
            texts: The texts to embed.
            **kwargs: Additional keyword arguments.

        Returns:
            A list of embedding results.

        Raises:
            ProviderError: If the provider is not initialized or if an error occurs.
        """
        raise NotImplementedError
