"""Example utilities."""

from collections.abc import AsyncGenerator
from typing import List, Optional, Type

from ..ai_types import Message, MessageRole
from ..exceptions import ProviderError
from ..responses import AIResponse
from ..providers.base import BaseProvider
from ..providers.config import ProviderConfig


class ExampleAIClient:
    """Example AI client implementation."""

    def __init__(self, provider: Type[BaseProvider[ProviderConfig]]) -> None:
        """Initialize example client.

        Args:
            provider: The provider class to use
        """
        self.config = ProviderConfig(
            name="example",
            version="1.0.0",
            enabled=True,
            api_key="example-key",
            model="gpt-3.5-turbo",
            provider="example",
            temperature=0.7,
            max_tokens=100,
        )
        self._provider_class = provider
        self._provider: Optional[BaseProvider[ProviderConfig]] = None

    async def initialize(self) -> None:
        """Initialize the client."""
        if not self._provider:
            self._provider = self._provider_class(self.config, self.config.api_key)
            await self._provider.initialize()

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        if self._provider:
            await self._provider.cleanup()
            self._provider = None

    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from provider.

        Args:
            prompt: The prompt to send to the provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self._provider:
            raise ProviderError("Provider not initialized", "example")

        messages = [Message(role=MessageRole.USER, content=prompt)]
        
        # Get the stream from the provider
        provider_stream = self._provider.stream(
            messages,
            model=model or self.config.model,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )

        # Yield responses from the stream
        async for response in provider_stream:
            yield response
