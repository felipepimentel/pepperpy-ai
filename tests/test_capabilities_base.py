"""Test base capability functionality."""

from collections.abc import AsyncGenerator
from typing import Any, cast

from pepperpy.capabilities.base import BaseCapability
from pepperpy.config.capability import CapabilityConfig
from pepperpy.providers.base import BaseProvider
from pepperpy.providers.config import ProviderConfig
from pepperpy.responses import ResponseData, ResponseMetadata
from pepperpy.types import Message


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
    ) -> AsyncGenerator[ResponseData, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding ResponseData objects
        """
        yield ResponseData(
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
        provider_config: ProviderConfig = {
            "name": "test-provider",
            "version": "1.0.0",
            "api_base": "https://api.test.com",
            "model": "test-model",
            "api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "timeout": 30.0,
        }
        self._provider = TestProvider(provider_config)

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
    ) -> AsyncGenerator[ResponseData, None]:
        """Stream responses from the capability.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional capability-specific parameters

        Returns:
            AsyncGenerator yielding ResponseData objects
        """
        async for response in self._provider.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield response
