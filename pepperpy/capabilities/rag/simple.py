"""Simple RAG capability module."""

from collections.abc import AsyncGenerator, Coroutine
from typing import Any, cast

from ...config.embeddings import EmbeddingsConfig
from ...embeddings.providers.sentence_transformers import SentenceTransformersProvider
from ...responses import AIResponse
from ...types import Message
from ..chat.base import BaseChatCapability
from .base import RAGCapability


class SimpleRAGCapability(RAGCapability):
    """Simple RAG capability."""

    def __init__(
        self, config: dict[str, Any], chat_capability: BaseChatCapability
    ) -> None:
        """Initialize the capability.

        Args:
            config: RAG configuration.
            chat_capability: Chat capability to use for responses.
        """
        super().__init__(config, chat_capability)
        self._initialized = False
        self._embeddings_provider: SentenceTransformersProvider | None = None

    @property
    def is_initialized(self) -> bool:
        """Return whether the capability is initialized.

        Returns:
            bool: Whether the capability is initialized.
        """
        return self._initialized and self._embeddings_provider is not None

    async def initialize(self) -> None:
        """Initialize the capability."""
        if not self.is_initialized:
            embeddings_config = cast(
                EmbeddingsConfig,
                {
                    "name": self.config.get("name", "simple"),
                    "version": self.config.get("version", "latest"),
                    "model": self.config.get("model", "all-MiniLM-L6-v2"),
                    "api_key": self.config.get("api_key", ""),
                    "provider_type": self.config.get("provider_type", "simple"),
                    "enabled": self.config.get("enabled", True),
                    "normalize": self.config.get("normalize", True),
                    "batch_size": self.config.get("batch_size", 32),
                    "device": self.config.get("device", "cpu"),
                },
            )
            self._embeddings_provider = SentenceTransformersProvider(embeddings_config)
            await self._embeddings_provider.initialize()
            await self.chat_capability.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up the capability."""
        if self.is_initialized and self._embeddings_provider is not None:
            await self._embeddings_provider.cleanup()
            await self.chat_capability.cleanup()
            self._embeddings_provider = None
            self._initialized = False

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            list[float]: Generated embeddings.
        """
        if not self.is_initialized or self._embeddings_provider is None:
            raise RuntimeError("Capability not initialized")
        return await self._embeddings_provider.embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[list[float]]: Generated embeddings for each text.
        """
        if not self.is_initialized or self._embeddings_provider is None:
            raise RuntimeError("Capability not initialized")
        return await self._embeddings_provider.embed_batch(texts)

    def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Coroutine[Any, Any, AsyncGenerator[AIResponse, None]]:
        """Stream responses from the capability.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional capability-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            NotImplementedError: This capability does not support streaming.
        """
        raise NotImplementedError("SimpleRAGCapability does not support streaming")
