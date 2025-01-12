"""Anthropic provider module."""

from collections.abc import AsyncGenerator
from typing import List, Optional

from anthropic import AsyncAnthropic

from ..ai_types import Message
from ..exceptions import ProviderError
from ..responses import AIResponse
from .base import BaseProvider
from .config import ProviderConfig


class AnthropicProvider(BaseProvider[ProviderConfig]):
    """Anthropic provider implementation."""

    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration
            api_key: API key for provider
        """
        super().__init__(config, api_key)
        self._client: Optional[AsyncAnthropic] = None

    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        if not self.api_key:
            raise ProviderError("API key not provided", "anthropic")
        self._client = AsyncAnthropic(api_key=self.api_key)
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup Anthropic client."""
        if self._client:
            await self._client.close()
            self._client = None
        self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from Anthropic.

        Args:
            messages: List of messages to send to Anthropic
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or client errors occur
        """
        if not self._client:
            raise ProviderError("Client not initialized", provider="anthropic")

        try:
            model = model or self.config.model
            temperature = temperature or self.config.temperature
            max_tokens = max_tokens or self.config.max_tokens

            # Convert messages to Anthropic format
            prompt = "\n\n".join(
                f"{msg.role.value.lower()}: {msg.content}"
                for msg in messages
            )

            async with self._client.messages.stream(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for chunk in stream:
                    if chunk.delta.text:
                        yield AIResponse(
                            content=chunk.delta.text,
                            model=model,
                            provider="anthropic"
                        )
        except Exception as e:
            raise ProviderError(f"Anthropic streaming error: {str(e)}", provider="anthropic")
