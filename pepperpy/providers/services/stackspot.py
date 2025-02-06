"""StackSpot provider implementation for the Pepperpy framework.

This module provides integration with StackSpot's API, supporting both completion
and streaming capabilities.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from pydantic import SecretStr

from pepperpy.monitoring import logger
from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderError,
    ProviderInitError,
    ProviderRateLimitError,
)

# Type aliases
JsonDict = dict[str, Any]


class StackSpotProvider(BaseProvider):
    """Provider implementation for StackSpot AI API.

    This provider implements the Provider protocol for StackSpot's API, supporting:
    - Chat completions with GPT-4 and other models
    - Text embeddings with Ada
    - Streaming responses
    - Rate limit handling
    - Proper error propagation

    Attributes:
        config (ProviderConfig): The provider configuration
        _session (ClientSession | None): The aiohttp session
        _model (str): The model to use
        _timeout (ClientTimeout): Request timeout configuration
        BASE_URL (str): StackSpot API base URL
    """

    BASE_URL: str = "https://api.stackspot.com/v1"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the StackSpot provider.

        Args:
            config: Provider configuration containing API key and other settings

        Note:
            The provider is not ready for use until initialize() is called.
        """
        super().__init__(config)
        self._session: ClientSession | None = None
        self._model: str = config.model or "gpt-4"
        self._timeout: ClientTimeout = ClientTimeout(total=config.timeout)
        self._api_key: SecretStr | None = None
        self._base_url = "https://api.stackspot.com"

    async def initialize(self) -> None:
        """Initialize the StackSpot client.

        This method sets up the aiohttp session with the required headers
        and authentication for StackSpot's API.

        Raises:
            ProviderInitError: If initialization fails
        """
        if not self.config.api_key:
            raise ProviderInitError(
                "API key is required",
                provider_type="stackspot",
            )

        try:
            self._api_key = self.config.api_key
            self._session = ClientSession(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
            )
            logger.info("Initialized StackSpot provider")
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize StackSpot provider: {e}",
                provider_type="stackspot",
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources by closing the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("StackSpot provider cleaned up")

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the StackSpot API.

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
            raise ProviderError(
                "Client not initialized",
                provider_type=self.config.provider_type,
            )

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

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
        """
        if not self._session:
            raise ProviderInitError(
                "StackSpot provider not initialized",
                provider_type="stackspot",
            )

        try:
            async with self._session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
            ) as response:
                if response.status != 200:
                    logger.warning(
                        "StackSpot API error",
                        extra={
                            "status": response.status,
                            "response": await response.text(),
                        },
                    )
                    raise ProviderAPIError(
                        f"StackSpot API error: {response.status}",
                        provider_type="stackspot",
                    )

                try:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    if not isinstance(content, str):
                        raise ProviderAPIError(
                            "Unexpected response format: content is not a string",
                            provider_type="stackspot",
                        )
                    return content
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(
                        "Failed to parse StackSpot response",
                        extra={
                            "error": str(e),
                            "response": await response.text(),
                        },
                    )
                    raise ProviderAPIError(
                        f"Failed to parse StackSpot response: {e}",
                        provider_type="stackspot",
                    ) from e

        except aiohttp.ClientError as e:
            raise ProviderAPIError(
                f"StackSpot API request failed: {e}",
                provider_type="stackspot",
            ) from e

    async def _stream_response(
        self, payload: dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Stream response from StackSpot.

        Args:
            payload: Request payload

        Yields:
            Text chunks as they are generated

        Raises:
            ProviderAPIError: If streaming fails
        """
        if not self._session:
            raise ProviderInitError(
                "StackSpot provider not initialized",
                provider_type="stackspot",
            )

        try:
            async with self._session.post(
                f"{self.BASE_URL}/chat/completions/stream",
                json=payload,
            ) as response:
                if response.status != 200:
                    logger.warning(
                        "StackSpot API error",
                        extra={
                            "status": response.status,
                            "response": await response.text(),
                        },
                    )
                    raise ProviderAPIError(
                        f"StackSpot API error: {response.status}",
                        provider_type="stackspot",
                    )

                async for line in response.content.iter_any():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if text := chunk["choices"][0]["delta"].get("content"):
                                yield text
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "Failed to parse streaming chunk",
                                extra={
                                    "error": str(e),
                                    "chunk": line.decode(),
                                },
                            )

        except aiohttp.ClientError as e:
            raise ProviderAPIError(
                f"StackSpot streaming request failed: {e}",
                provider_type="stackspot",
            ) from e

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text using StackSpot.

        Args:
            text: Text to generate embeddings for
            **kwargs: Additional provider-specific parameters.
                     The 'model' parameter can be used to specify the embedding model.

        Returns:
            List of floating point values representing the text embedding

        Raises:
            ProviderAPIError: If the embedding generation fails
            ProviderInitError: If the session is not initialized
            ProviderRateLimitError: If rate limit is exceeded

        Example:
            ```python
            # Default model (Ada)
            embedding = await provider.embed("Hello world")

            # Custom model
            embedding = await provider.embed(
                "Hello world",
                model="text-embedding-ada-002"
            )
            ```
        """
        if not self._session:
            raise ProviderInitError(
                "StackSpot provider not initialized", provider_type="stackspot"
            )

        payload: JsonDict = {
            "model": kwargs.get("model", "text-embedding-ada-002"),
            "input": text,
        }

        try:
            async with self._session.post(
                f"{self.BASE_URL}/embeddings", json=payload, raise_for_status=False
            ) as response:
                if not response.ok:
                    error_msg = (
                        f"StackSpot API request failed: {response.text} "
                        f"(status: {response.status})"
                    )
                    logger.warning(message=error_msg)
                    raise ProviderError(
                        f"StackSpot API request failed: {response.text}",
                        provider_type="stackspot",
                    )

                data = await response.json()
                embeddings: list[float] = data["data"][0]["embedding"]
                return embeddings

        except ProviderRateLimitError:
            raise
        except Exception as e:
            raise ProviderAPIError(
                f"StackSpot embedding error: {e!s}",
                provider_type="stackspot",
                details={"error": str(e)},
            ) from e
