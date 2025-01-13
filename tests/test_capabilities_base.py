"""Test base capability functionality."""

from collections.abc import AsyncGenerator
from typing import Any, cast

from pepperpy_ai.capabilities.base import BaseCapability
from pepperpy_ai.capabilities.config import CapabilityConfig
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.providers.config import ProviderConfig
from pepperpy_ai.responses import AIResponse, ResponseMetadata
from pepperpy_ai.types import Message


class TestProvider(BaseProvider[ProviderConfig]):
    """Test provider implementation."""

    async def initialize(self) -> None:
        """Initialize provider."""
        pass

    async def cleanup(self) -> None:
        """Cleanup provider."""
        pass

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        yield AIResponse(
            content="Hello, how can I help you?",
            metadata=cast(ResponseMetadata, {"model": "test", "provider": "test"}),
        )


class TestCapability(BaseCapability[CapabilityConfig]):
    """Test capability implementation."""

    def __init__(self, config: CapabilityConfig) -> None:
        """Initialize test capability.

        Args:
            config: Capability configuration
        """
        super().__init__(config)
        self._provider = TestProvider(config)

    async def initialize(self) -> None:
        """Initialize capability."""
        await self._provider.initialize()

    async def cleanup(self) -> None:
        """Cleanup capability."""
        await self._provider.cleanup()

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
        async for response in self._provider.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield response
