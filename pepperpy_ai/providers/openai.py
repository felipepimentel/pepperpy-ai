"""OpenAI provider implementation."""

import importlib.util
from collections.abc import AsyncGenerator
from typing import Any, NotRequired, TypedDict, cast

from ..exceptions import DependencyError
from ..ai_types import Message
from ..responses import AIResponse, ResponseMetadata
from .base import BaseProvider
from .exceptions import ProviderError


def _check_openai_dependency() -> None:
    """Check if OpenAI package is installed.

    Raises:
        DependencyError: If OpenAI package is not installed.
    """
    if importlib.util.find_spec("openai") is None:
        raise DependencyError(
            feature="OpenAI provider",
            package="openai",
            extra="openai",
        )


class OpenAIConfig(TypedDict):
    """OpenAI provider configuration."""

    model: str  # Required field
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]


class OpenAIProvider(BaseProvider[OpenAIConfig]):
    """OpenAI provider implementation."""

    def __init__(self, config: OpenAIConfig, api_key: str) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
            api_key: OpenAI API key

        Raises:
            DependencyError: If OpenAI package is not installed
        """
        _check_openai_dependency()
        super().__init__(config, api_key)
        self._client: Any = None  # Type will be AsyncOpenAI when imported

    @property
    def client(self) -> Any:  # Type will be AsyncOpenAI when imported
        """Get client instance.

        Returns:
            AsyncOpenAI: Client instance.

        Raises:
            ProviderError: If provider is not initialized.
        """
        if not self.is_initialized or not self._client:
            raise ProviderError(
                "Provider not initialized",
                provider="openai",
                operation="get_client",
            )
        return self._client

    async def initialize(self) -> None:
        """Initialize provider."""
        if not self._initialized:
            _check_openai_dependency()
            from openai import AsyncOpenAI
            
            timeout = self.config.get("timeout", 30.0)
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=timeout,
            )
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._client:
            await self._client.close()
        self._initialized = False
        self._client = None

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from OpenAI.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or streaming fails
            DependencyError: If OpenAI package is not installed
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized",
                provider="openai",
                operation="stream",
            )

        try:
            async with self.client.chat.completions.stream(
                messages=[
                    {"role": msg.role.value.lower(), "content": msg.content}
                    for msg in messages
                ],
                model=model or self.config["model"],
                temperature=temperature or self.config.get("temperature", 0.7),
                max_tokens=max_tokens or self.config.get("max_tokens", 1000),
                stream=True,
            ) as stream:
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield AIResponse(
                            content=chunk.choices[0].delta.content,
                            metadata=cast(ResponseMetadata, {
                                "model": model or self.config["model"],
                                "provider": "openai",
                                "usage": {"total_tokens": 0},
                                "finish_reason": chunk.choices[0].finish_reason or None,
                            }),
                        )
        except Exception as e:
            raise ProviderError(
                f"Failed to stream responses: {str(e)}",
                provider="openai",
                operation="stream",
                cause=e,
            ) from e
