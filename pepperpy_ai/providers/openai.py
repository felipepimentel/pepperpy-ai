"""OpenAI provider module."""

from collections.abc import AsyncGenerator
from typing import List, Optional

from openai import AsyncOpenAI

from ..ai_types import Message
from ..exceptions import ProviderError
from ..responses import AIResponse
from .base import BaseProvider
from .config import ProviderConfig


class OpenAIProvider(BaseProvider[ProviderConfig]):
    """OpenAI provider implementation."""

    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
            api_key: API key for provider
        """
        super().__init__(config, api_key)
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        if not self.api_key:
            raise ProviderError("API key not provided", "openai")
        self._client = AsyncOpenAI(api_key=self.api_key)
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup OpenAI client."""
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
        """Stream responses from OpenAI.

        Args:
            messages: List of messages to send to OpenAI
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or client errors occur
        """
        if not self._client:
            raise ProviderError("Client not initialized", provider="openai")

        try:
            model = model or self.config.model
            temperature = temperature or self.config.temperature
            max_tokens = max_tokens or self.config.max_tokens

            async with self._client.chat.completions.create(
                model=model,
                messages=[{"role": msg.role.value.lower(), "content": msg.content} for msg in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            ) as stream:
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield AIResponse(
                            content=chunk.choices[0].delta.content,
                            model=model,
                            provider="openai"
                        )
        except Exception as e:
            raise ProviderError(f"OpenAI streaming error: {str(e)}", provider="openai")
