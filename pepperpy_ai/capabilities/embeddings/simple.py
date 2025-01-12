"""Simple embeddings capability module."""

from typing import Any, Dict, List, Optional, Type

from ...ai_types import Message
from ...responses import AIResponse
from ...exceptions import CapabilityError
from ...embeddings.providers.base import BaseEmbeddingsProvider
from ..base import CapabilityConfig
from .base import BaseEmbeddingsCapability


class SimpleEmbeddingsCapability(BaseEmbeddingsCapability):
    """Simple embeddings capability implementation."""

    def __init__(self, config: CapabilityConfig, provider: Type[BaseEmbeddingsProvider]) -> None:
        """Initialize embeddings capability.

        Args:
            config: Capability configuration
            provider: Embeddings provider class to use
        """
        super().__init__(config, provider)
        self._embeddings: Dict[str, List[float]] = {}

    async def embed(self, text: str) -> List[float]:
        """Embed text into vector.

        Args:
            text: Text to embed

        Returns:
            List of embedding values

        Raises:
            CapabilityError: If provider is not initialized
        """
        if not self._provider_instance:
            await self.initialize()
        if not self._provider_instance:
            raise CapabilityError("Provider not initialized", "embeddings")
        return await self._provider_instance.embed(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts into vectors.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            CapabilityError: If provider is not initialized
        """
        if not self._provider_instance:
            await self.initialize()
        if not self._provider_instance:
            raise CapabilityError("Provider not initialized", "embeddings")
        return await self._provider_instance.embed_batch(texts)
