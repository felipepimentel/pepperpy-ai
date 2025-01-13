"""Base chat capability module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import cast

from ...config.capability import CapabilityConfig
from ...messages import Message
from ...providers.base import BaseProvider
from ...responses import AIResponse, ResponseMetadata
from ..base import BaseCapability


class ChatConfig(CapabilityConfig):
    """Chat configuration."""

    pass


class ChatCapability(BaseCapability[BaseProvider], ABC):
    """Base chat capability implementation."""

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        timeout: float | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream chat messages.

        Args:
            messages: List of messages to stream
            model: Model to use for generation
            temperature: Temperature for generation
            max_tokens: Maximum number of tokens to generate
            top_p: Top p for generation
            frequency_penalty: Frequency penalty for generation
            presence_penalty: Presence penalty for generation
            timeout: Timeout for generation

        Yields:
            AIResponse: Generated response
        """
        if not self.is_initialized:
            raise RuntimeError("Capability not initialized")

        yield AIResponse(
            content="Hello, how can I help you?",
            metadata=cast(ResponseMetadata, {
                "model": model or self.config.model,
                "provider": "chat",
                "usage": {"total_tokens": 0},
                "finish_reason": "stop",
            }),
        )
