"""StackSpot provider implementation."""

import json
from collections.abc import AsyncGenerator

import aiohttp

from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider, ProviderConfig
from .exceptions import ProviderError


class StackSpotProvider(BaseProvider[ProviderConfig]):
    """StackSpot provider implementation."""

    BASE_URL = "https://api.stackspot.com/v1"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize StackSpot provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._initialized = False
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the HTTP session.

        Returns:
            The HTTP session

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self._session:
            raise ProviderError(
                "Provider not initialized",
                provider="stackspot",
                operation="session",
            )
        return self._session

    async def initialize(self) -> None:
        """Initialize provider resources."""
        if not self._initialized:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.get('api_key', '')}",
                    "Content-Type": "application/json",
                }
            )
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._initialized and self._session:
            await self._session.close()
            self._session = None
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized.

        Returns:
            True if provider is initialized, False otherwise
        """
        return self._initialized

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from StackSpot.

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
            raise ProviderError(
                "Provider not initialized",
                provider="stackspot",
                operation="stream",
            )

        try:
            async with self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "messages": [
                        {"role": msg.role.value.lower(), "content": msg.content}
                        for msg in messages
                    ],
                    "model": model or self.config.get("model", ""),
                    "temperature": temperature or self.config.get("temperature", 0.7),
                    "max_tokens": max_tokens or self.config.get("max_tokens", 1000),
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.content:
                    line = line.strip()
                    if not line or line == b"data: [DONE]":
                        continue
                    if not line.startswith(b"data: "):
                        continue
                    data = json.loads(line[6:])
                    if not data["choices"][0]["delta"].get("content"):
                        continue
                    yield AIResponse(
                        content=data["choices"][0]["delta"]["content"],
                        metadata={
                            "model": model or self.config.get("model", ""),
                            "provider": "stackspot",
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                            "finish_reason": data["choices"][0].get("finish_reason"),
                        },
                    )
        except Exception as e:
            raise ProviderError(
                "Failed to stream responses",
                provider="stackspot",
                operation="stream",
                cause=e,
            ) from e
