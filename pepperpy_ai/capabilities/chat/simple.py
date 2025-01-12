"""Simple chat capability implementation."""

from collections.abc import AsyncGenerator
from typing import Any, List, Optional, Type

from ...ai_types import Message
from ...exceptions import CapabilityError
from ...providers.base import BaseProvider
from ...responses import AIResponse
from .base import ChatCapability, ChatConfig


class SimpleChatCapability(ChatCapability):
    """Simple chat capability implementation."""

    def __init__(self, config: ChatConfig, provider: Type[BaseProvider[Any]]) -> None:
        """Initialize capability.

        Args:
            config: Chat configuration
            provider: Provider class to use
        """
        super().__init__(config, provider)
        self._provider_instance: Optional[BaseProvider[Any]] = None

    async def initialize(self) -> None:
        """Initialize capability."""
        if not self._provider_instance:
            self._provider_instance = self.provider(self.config, self.config.api_key)
            await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup capability resources."""
        if self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None
            self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send to the provider
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            CapabilityError: If capability is not initialized
        """
        if not self.is_initialized:
            raise CapabilityError("Capability not initialized", "chat")

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
            raise CapabilityError(f"Error streaming responses: {str(e)}", "chat")
