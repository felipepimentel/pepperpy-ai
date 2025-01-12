"""OpenRouter provider module."""

from collections.abc import AsyncGenerator
from typing import List, Optional

import aiohttp
import json

from ..ai_types import Message
from ..exceptions import ProviderError
from ..responses import AIResponse
from .base import BaseProvider
from .config import ProviderConfig


class OpenRouterProvider(BaseProvider[ProviderConfig]):
    """OpenRouter provider implementation."""

    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        """Initialize OpenRouter provider.

        Args:
            config: Provider configuration
            api_key: API key for provider
        """
        super().__init__(config, api_key)
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize OpenRouter client."""
        if not self.api_key:
            raise ProviderError("API key not provided", "openrouter")
        self._session = aiohttp.ClientSession()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup OpenRouter client."""
        if self._session:
            await self._session.close()
            self._session = None
        self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from OpenRouter.

        Args:
            messages: List of messages to send to OpenRouter
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or client errors occur
        """
        if not self._session:
            raise ProviderError("Client not initialized", provider="openrouter")

        try:
            model = model or self.config.model
            temperature = temperature or self.config.temperature
            max_tokens = max_tokens or self.config.max_tokens

            async with self._session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": msg.role.value.lower(), "content": msg.content} for msg in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = line.decode().strip()
                            if data.startswith("data: "):
                                data = data[6:]
                                if data == "[DONE]":
                                    break
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"][0]["delta"].get("content"):
                                    yield AIResponse(
                                        content=chunk["choices"][0]["delta"]["content"],
                                        model=model,
                                        provider="openrouter"
                                    )
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
        except Exception as e:
            raise ProviderError(f"OpenRouter streaming error: {str(e)}", provider="openrouter")
