"""Base LLM module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import cast

from ..messages import Message
from ..responses import AIResponse, ResponseMetadata


class BaseLLM(ABC):
    """Base LLM implementation."""

    def __init__(self) -> None:
        """Initialize LLM."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if LLM is initialized.

        Returns:
            bool: True if LLM is initialized, False otherwise.
        """
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize LLM."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up LLM resources."""
        pass

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
        """Stream LLM messages.

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
            raise RuntimeError("LLM not initialized")

        yield AIResponse(
            content="Hello, how can I help you?",
            metadata=cast(ResponseMetadata, {
                "model": model,
                "provider": "llm",
                "usage": {"total_tokens": 0},
                "finish_reason": "stop",
            }),
        )
