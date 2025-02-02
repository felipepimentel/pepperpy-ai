"""OpenRouter provider implementation for Pepperpy.

This module provides integration with OpenRouter's API for accessing
various language models through a unified interface.
"""

from collections.abc import AsyncGenerator
from typing import Any, cast

import aiohttp
from pydantic import SecretStr

from pepperpy.monitoring import logger
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)
from pepperpy.providers.provider import BaseProvider, ProviderConfig


class OpenRouterProvider(BaseProvider):
    """Provider implementation for OpenRouter's API.

    This provider implements the Provider protocol for OpenRouter's API,
    supporting:
    - Text generation with various models
    - Streaming responses
    - Rate limit handling
    - Proper error propagation
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the OpenRouter provider.

        Args:
            config: Provider configuration containing API key and other settings

        Note:
            The provider is not ready for use until initialize() is called
        """
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._api_key: SecretStr | None = None
        self._base_url = "https://openrouter.ai/api/v1"

    async def initialize(self) -> None:
        """Initialize the OpenRouter client.

        This method sets up the HTTP session and validates the API key.

        Raises:
            ProviderInitError: If initialization fails
        """
        if not self.config.api_key:
            raise ProviderInitError(
                "API key is required",
                provider_type="openrouter",
            )

        try:
            self._api_key = self.config.api_key
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "Pepperpy",
                }
            )
            logger.info("Initialized OpenRouter provider")
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize OpenRouter provider: {e}",
                provider_type="openrouter",
            ) from e

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the OpenRouter API.

        Args:
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails
        """
        if not self._session:
            raise ProviderInitError(
                "OpenRouter provider not initialized",
                provider_type="openrouter",
            )

        payload = {
            "model": self.config.model or "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens if max_tokens is not None else None,
            "stream": stream,
            **kwargs,
        }

        if stream:
            return self._stream_response(payload)
        return await self._complete_sync(payload)

    async def _complete_sync(self, payload: dict[str, Any]) -> str:
        """Send a synchronous completion request.

        Args:
            payload: Request payload

        Returns:
            Generated text

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self._session:
            raise ProviderInitError(
                "OpenRouter provider not initialized",
                provider_type="openrouter",
            )

        try:
            async with self._session.post(
                f"{self._base_url}/chat/completions",
                json=payload,
            ) as response:
                if response.status == 429:
                    raise ProviderRateLimitError(
                        "OpenRouter rate limit exceeded",
                        provider_type="openrouter",
                    )

                if response.status != 200:
                    text = await response.text()
                    logger.warning(
                        "OpenRouter API error",
                        extra={
                            "status": response.status,
                            "response": text,
                        },
                    )
                    raise ProviderAPIError(
                        f"OpenRouter API error: {response.status}",
                        provider_type="openrouter",
                    )

                result = await response.json()
                content = cast(str, result["choices"][0]["message"]["content"])
                return content

        except aiohttp.ClientError as e:
            raise ProviderAPIError(
                f"OpenRouter API request failed: {e}",
                provider_type="openrouter",
            ) from e

    async def _stream_response(
        self,
        payload: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenRouter.

        Args:
            payload: Request payload

        Yields:
            Text chunks as they are generated

        Raises:
            ProviderAPIError: If streaming fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self._session:
            raise ProviderInitError(
                "OpenRouter provider not initialized",
                provider_type="openrouter",
            )

        try:
            async with self._session.post(
                f"{self._base_url}/chat/completions",
                json=payload,
            ) as response:
                if response.status == 429:
                    raise ProviderRateLimitError(
                        "OpenRouter rate limit exceeded",
                        provider_type="openrouter",
                    )

                if response.status != 200:
                    text = await response.text()
                    logger.warning(
                        "OpenRouter API error",
                        extra={
                            "status": response.status,
                            "response": text,
                        },
                    )
                    raise ProviderAPIError(
                        f"OpenRouter API error: {response.status}",
                        provider_type="openrouter",
                    )

                async for line in response.content.iter_chunks():
                    if line and line[0].startswith(b"data: "):
                        try:
                            chunk = line[0][6:].decode("utf-8")
                            if chunk == "[DONE]":
                                break

                            result = await response.json()
                            if content := result["choices"][0]["delta"].get("content"):
                                yield content
                        except Exception as e:
                            logger.warning(
                                "Failed to parse streaming chunk",
                                extra={
                                    "error": str(e),
                                    "chunk": line[0].decode(),
                                },
                            )

        except aiohttp.ClientError as e:
            raise ProviderAPIError(
                f"OpenRouter streaming request failed: {e}",
                provider_type="openrouter",
            ) from e

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method ensures proper cleanup of HTTP session and other resources.
        """
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("OpenRouter provider cleaned up")
