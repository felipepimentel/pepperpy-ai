"""OpenRouter provider implementation for Pepperpy.

This module provides integration with OpenRouter's API for accessing
various language models through a unified interface.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any, cast
from uuid import uuid4

import aiohttp
from pydantic import SecretStr

from pepperpy.core.types import Message, Response, ResponseStatus
from pepperpy.monitoring import logger
from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderInitError,
    ProviderRateLimitError,
)


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

    async def _handle_response_status(self, response: aiohttp.ClientResponse) -> None:
        """Handle response status codes.

        Args:
            response: The HTTP response

        Raises:
            ProviderRateLimitError: If rate limit is exceeded
            ProviderAPIError: If API returns an error
        """
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

    async def _process_chunk(self, line: bytes) -> str | None:
        """Process a single chunk from the stream.

        Args:
            line: Raw chunk data

        Returns:
            Processed content or None if chunk should be skipped
        """
        if not line.startswith(b"data: "):
            return None

        chunk = line[6:].decode("utf-8")
        if chunk == "[DONE]":
            return None

        try:
            result = json.loads(chunk)
            content = result["choices"][0]["delta"].get("content")
            return str(content) if content is not None else None
        except Exception as e:
            logger.warning(
                "Failed to parse streaming chunk",
                extra={
                    "error": str(e),
                    "chunk": chunk,
                },
            )
            return None

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
                await self._handle_response_status(response)

                async for line, _ in response.content.iter_chunks():
                    if content := await self._process_chunk(line):
                        yield content

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

    async def generate(self, messages: list[Message], **kwargs: Any) -> Response:
        """Generate a response from the provider.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the provider

        Returns:
            Generated response

        Raises:
            ProviderInitError: If the provider is not initialized
            ProviderAPIError: If the API request fails
            ProviderError: If generation fails for other reasons
        """
        self._ensure_initialized()

        # Convert messages to OpenRouter format
        prompt = "\n".join(msg.content.get("text", "") for msg in messages)
        response = await self.complete(prompt, stream=False, **kwargs)
        if isinstance(response, AsyncGenerator):
            raise TypeError("Provider returned a streaming response")

        return Response(
            id=uuid4(),
            message_id=messages[-1].id if messages else uuid4(),
            content={"text": response},
            status=ResponseStatus.SUCCESS,
            metadata={
                "provider": self.name,
                "model": self.config.model,
            },
        )

    def stream(
        self, messages: list[Message], **kwargs: Any
    ) -> AsyncGenerator[Response, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the provider

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            ProviderInitError: If the provider is not initialized
            ProviderAPIError: If the API request fails
            ProviderError: If streaming fails for other reasons
        """
        self._ensure_initialized()

        # Convert messages to OpenRouter format
        prompt = "\n".join(msg.content.get("text", "") for msg in messages)

        async def response_generator() -> AsyncGenerator[Response, None]:
            response = await self.complete(prompt, stream=True, **kwargs)
            if isinstance(response, AsyncGenerator):
                async for chunk in response:
                    if isinstance(chunk, str):
                        yield Response(
                            id=uuid4(),
                            message_id=messages[-1].id if messages else uuid4(),
                            content={"text": chunk},
                            status=ResponseStatus.SUCCESS,
                            metadata={
                                "provider": self.name,
                                "model": self.config.model,
                            },
                        )
            else:
                # If provider doesn't support streaming, yield the entire response
                yield Response(
                    id=uuid4(),
                    message_id=messages[-1].id if messages else uuid4(),
                    content={"text": response},
                    status=ResponseStatus.SUCCESS,
                    metadata={
                        "provider": self.name,
                        "model": self.config.model,
                    },
                )

        return response_generator()
