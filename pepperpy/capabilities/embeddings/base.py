"""Base embeddings capability implementation."""

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from ...responses import AIResponse
from ...types import Message
from ..base import BaseCapability


class BaseEmbeddingsCapability(BaseCapability):
    """Base embeddings capability implementation."""

    @abstractmethod
    async def embed(self, texts: list[str], **kwargs: Any) -> list[float]:
        """Embed texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional capability-specific parameters

        Returns:
            List of embeddings
        """
        raise NotImplementedError

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
        """
        raise NotImplementedError
