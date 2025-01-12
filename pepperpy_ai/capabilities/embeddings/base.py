"""Base classes for embedding capabilities."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, cast

from ...embeddings.base import EmbeddingsConfig
from ...embeddings.providers.base import BaseEmbeddingsProvider
from ..base import BaseCapability, CapabilityConfig


class BaseEmbeddingsCapability(BaseCapability[CapabilityConfig]):
    """Base class for embeddings capabilities."""

    def __init__(
        self,
        config: CapabilityConfig,
        provider: Type[BaseEmbeddingsProvider],
    ) -> None:
        """Initialize capability.

        Args:
            config: Capability configuration
            provider: Embeddings provider class
        """
        super().__init__(config, cast(Type[Any], provider))
        self._provider_instance: Optional[BaseEmbeddingsProvider] = None
        self._provider_class = provider

    async def initialize(self) -> None:
        """Initialize capability."""
        if not self._provider_instance:
            embeddings_config = EmbeddingsConfig(
                model_name=self.config.model_name,
                dimension=768,  # Default dimension
                device=self.config.device,
                normalize_embeddings=self.config.normalize_embeddings,
                batch_size=self.config.batch_size,
            )
            self._provider_instance = self._provider_class(embeddings_config)
            await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup capability resources."""
        if self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None
            self._initialized = False

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
