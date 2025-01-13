"""OpenRouter provider implementation."""

import json
import logging
from collections.abc import AsyncGenerator

import aiohttp

from ..responses import AIResponse
from ..types import Message
from .base import BaseProvider
from .config import ProviderConfig
from .exceptions import ProviderError

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseProvider[ProviderConfig]):
    """OpenRouter provider implementation."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get session instance.

        Returns:
            aiohttp.ClientSession: Session instance.

        Raises:
            ProviderError: If provider is not initialized.
        """
        if not self.is_initialized or not self._session:
            raise ProviderError("Provider is not initialized")
        return self._session

    async def initialize(self) -> None:
        """Initialize provider resources."""
        if not self._initialized:
            timeout = aiohttp.ClientTimeout(total=self.config.get("timeout", 30.0))
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.get('api_key', '')}",
                    "HTTP-Referer": "https://github.com/felipepimentel/pepperpy-ai",
                    "X-Title": "PepperPy AI",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._session:
            await self._session.close()
        self._initialized = False
        self._session = None

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from OpenRouter.

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
                            "provider": "openrouter",
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                            },
                            "finish_reason": data["choices"][0].get("finish_reason"),
                        },
                    )
        except Exception as e:
            raise ProviderError(f"Failed to stream responses: {e}") from e
