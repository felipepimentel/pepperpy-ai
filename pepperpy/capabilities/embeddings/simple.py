"""Simple embeddings capability module."""

from collections.abc import AsyncGenerator
from typing import Any, cast

from ...config.embeddings import EmbeddingsConfig
from ...embeddings.base import BaseEmbeddingsProvider
from ...responses import AIResponse
from ...types import Message


class SimpleEmbeddingsCapability(BaseEmbeddingsProvider):
    """Simple embeddings capability."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the capability.

        Args:
            config: Embeddings configuration.
        """
        embeddings_config = cast(
            EmbeddingsConfig,
            {
                "name": config["name"],
                "version": config["version"],
                "model": config["model"],
                "api_key": config.get("api_key", ""),
                "provider_type": config.get("provider_type", "simple"),
                "enabled": config.get("enabled", True),
                "normalize": config.get("normalize", True),
                "batch_size": config.get("batch_size", 32),
                "device": config.get("device", "cpu"),
                "api_base": config.get("api_base", ""),
                "api_version": config.get("api_version", ""),
                "organization": config.get("organization", ""),
                "temperature": config.get("temperature", 0.0),
                "max_tokens": config.get("max_tokens", 100),
                "top_p": config.get("top_p", 1.0),
                "frequency_penalty": config.get("frequency_penalty", 0.0),
                "presence_penalty": config.get("presence_penalty", 0.0),
                "timeout": config.get("timeout", 30.0),
            },
        )
        super().__init__(embeddings_config)
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the capability is initialized.

        Returns:
            bool: Whether the capability is initialized.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the capability."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up the capability."""
        self._initialized = False

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.

        Returns:
            list[float]: Generated embeddings.
        """
        return [0.0] * 10

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            list[list[float]]: Generated embeddings for each text.
        """
        return [[0.0] * 10 for _ in texts]

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
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
        raise NotImplementedError(
            "SimpleEmbeddingsCapability does not support streaming"
        )
