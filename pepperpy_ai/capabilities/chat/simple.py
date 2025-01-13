"""Simple chat capability implementation."""

from collections.abc import AsyncGenerator
from typing import Any

from ...ai_types import Message
from ...exceptions import CapabilityError
from ...providers.base import BaseProvider
from ...responses import AIResponse
from .base import ChatCapability, ChatConfig


class SimpleChatCapability(ChatCapability):
    """Simple chat capability implementation.

    This implementation provides basic chat functionality using
    a configurable provider.
    """

    def __init__(
        self,
        config: ChatConfig,
        provider: type[BaseProvider[Any]],
    ) -> None:
        """Initialize chat capability.

        Args:
            config: Capability configuration.
            provider: Provider class to use.
        """
        super().__init__(config, provider)
        self._provider_instance: BaseProvider[Any] | None = None

    async def initialize(self) -> None:
        """Initialize capability resources."""
        if not self.is_initialized:
            if not self._provider_instance:
                self._provider_instance = self.provider(
                    self.config,
                    api_key=self.config.api_key or "",
                )
                await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up capability resources."""
        if self.is_initialized:
            if self._provider_instance:
                await self._provider_instance.cleanup()
                self._provider_instance = None
            self._initialized = False

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
        """Stream responses from the provider.

        Args:
            messages: List of messages to generate response for.
            model: Model to use for generation.
            temperature: Temperature for generation.
            max_tokens: Maximum number of tokens to generate.
            top_p: Top p for generation.
            frequency_penalty: Frequency penalty for generation.
            presence_penalty: Presence penalty for generation.
            timeout: Timeout for generation.

        Returns:
            AsyncGenerator[AIResponse, None]: Generated responses.

        Raises:
            CapabilityError: If provider is not initialized or streaming fails.
        """
        self._ensure_initialized()
        if not self._provider_instance:
            raise CapabilityError("Provider not initialized", "chat")

        try:
            async for response in self._provider_instance.stream(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield response
        except Exception as e:
            raise CapabilityError(f"Error streaming responses: {e!s}", "chat") from e
