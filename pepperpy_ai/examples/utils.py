"""Example utilities."""

from collections.abc import AsyncGenerator

from ..ai_types import Message, MessageRole
from ..exceptions import ProviderError
from ..providers.base import BaseProvider
from ..providers.config import ProviderConfig
from ..responses import AIResponse


class ExampleAIClient:
    """Example AI client implementation."""

    def __init__(self, provider: type[BaseProvider[ProviderConfig]]) -> None:
        """Initialize example client.

        Args:
            provider: The provider class to use
        """
        self.config = ProviderConfig(
            api_key="example-key",
            model="gpt-3.5-turbo",
            timeout=30.0,
            max_retries=3,
            retry_delay=1.0,
        )
        self._provider_class = provider
        self._provider: BaseProvider[ProviderConfig] | None = None

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
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
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
            raise ProviderError("Provider not initialized", provider="example")

        messages = [Message(role=MessageRole.USER, content=prompt)]

        # Get the stream from the provider
        provider_stream = self._provider.stream(
            messages,
            model=model or self.config.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Yield responses from the stream
        async for response in provider_stream:
            yield response
