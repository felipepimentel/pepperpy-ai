"""OpenAI provider implementation."""

from collections.abc import AsyncGenerator
from typing import cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider
from .config import ProviderConfig
from .exceptions import ProviderError


class OpenAIProvider(BaseProvider[ProviderConfig]):
    """OpenAI provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=self.config.get("api_key", ""))
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider resources."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or streaming fails
        """
        if not self.is_initialized:
            raise ProviderError("Provider is not initialized")

        try:
            chat_messages = [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in messages
            ]

            stream = await self.client.chat.completions.create(
                model=model or self.config.get("model", "gpt-3.5-turbo"),
                messages=cast(list[ChatCompletionMessageParam], chat_messages),
                temperature=temperature or self.config.get("temperature", 0.7),
                max_tokens=max_tokens or self.config.get("max_tokens", 1000),
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield AIResponse(
                        content=chunk.choices[0].delta.content,
                        metadata={
                            "model": model or self.config.get("model", "gpt-3.5-turbo"),
                            "provider": "openai",
                            "finish_reason": chunk.choices[0].finish_reason,
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                            },
                        },
                    )
        except Exception as e:
            raise ProviderError(f"Failed to stream responses: {e}") from e
