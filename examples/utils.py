"""Example utilities."""

from collections.abc import AsyncGenerator

from pepperpy_ai.ai_types import Message
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.providers.config import ProviderConfig
from pepperpy_ai.responses import AIResponse


class ExampleAIClient:
    """Example AI client."""

    def __init__(self, provider: type[BaseProvider[ProviderConfig]]) -> None:
        """Initialize client.

        Args:
            provider: Provider class to use
        """
        self.provider = provider
        self._provider_instance: BaseProvider[ProviderConfig] | None = None

    async def initialize(self) -> None:
        """Initialize client."""
        if not self._provider_instance:
            config = ProviderConfig(
                provider="mock",
                api_key="mock-key",
                model="mock-model",
            )
            self._provider_instance = self.provider(config, config.api_key)
            await self._provider_instance.initialize()

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        if self._provider_instance:
            await self._provider_instance.cleanup()
            self._provider_instance = None

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from provider.

        Args:
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self._provider_instance:
            raise ProviderError("Provider not initialized", "example")

        # Get the stream from the provider
        provider_stream = self._provider_instance.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Yield responses from the stream
        async for response in provider_stream:
            yield response
