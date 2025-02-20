"""StackSpot provider implementation for the Pepperpy framework.

This module provides integration with StackSpot's API for accessing
various language models through a unified interface.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any, Dict, Union, cast

import aiohttp
from pydantic import SecretStr

from pepperpy.agents.providers.domain import ProviderRateLimitError
from pepperpy.core.messages import ProviderMessage, ProviderResponse
from pepperpy.core.providers.base import BaseProvider, ProviderConfig
from pepperpy.core.providers.errors import (
    ProviderResourceError as ProviderInitError,
)
from pepperpy.core.providers.errors import (
    ProviderRuntimeError as ProviderAPIError,
)

# Configure logger
logger = logging.getLogger(__name__)

# Type aliases for provider parameters
GenerateKwargs = Dict[str, Any]
StreamKwargs = Dict[str, Any]
EmbeddingKwargs = Dict[str, Any]


class StackSpotProvider(BaseProvider):
    """Provider implementation for StackSpot's API.

    This provider implements the Provider protocol for StackSpot's API,
    supporting:
    - Text generation with various models
    - Streaming responses
    - Rate limit handling
    - Proper error propagation
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the StackSpot provider.

        Args:
            config: Provider configuration

        Note:
            The provider is not ready for use until initialize() is called
        """
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._base_url = config.config.get("base_url", "https://api.stackspot.com/v1")
        self._api_key = SecretStr(config.config.get("api_key", ""))
        self._model = config.config.get("model", "gpt-4")
        self._extra_config = config.config.get("extra_config", {})

    async def initialize(self) -> None:
        """Initialize the StackSpot client.

        This method sets up the HTTP session and validates the API key.

        Raises:
            ProviderInitError: If initialization fails
        """
        try:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                }
            )
            logger.info("Initialized StackSpot provider")
        except Exception as e:
            raise ProviderInitError(
                message=f"Failed to initialize StackSpot provider: {e}",
                provider_type="stackspot",
            ) from e

    async def complete(
        self,
        prompt: str,
        *,
        kwargs: GenerateKwargs | None = None,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the StackSpot API.

        Args:
            prompt: The prompt to complete
            kwargs: Provider-specific parameters defined in ProviderKwargs

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails
        """
        if not self._session:
            raise ProviderInitError(
                message="StackSpot provider not initialized",
                provider_type="stackspot",
            )

        kwargs = kwargs or {}
        model_params = self._extra_config.get("model_params", {})
        excluded_params = ("temperature", "max_tokens", "stream")
        extra_params = {k: v for k, v in kwargs.items() if k not in excluded_params}
        payload = {
            "model": model_params.get("model", self._model),
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens"),
            "stream": kwargs.get("stream", False),
            **extra_params,
        }

        try:
            async with self._session.post(
                f"{self._base_url}/completions",
                json=payload,
            ) as response:
                if response.status == 429:
                    raise ProviderRateLimitError(
                        message="StackSpot rate limit exceeded",
                        provider_type="stackspot",
                    )

                if response.status != 200:
                    text = await response.text()
                    logger.warning(
                        "StackSpot API error",
                        extra={
                            "status": str(response.status),
                            "response": text,
                        },
                    )
                    raise ProviderAPIError(
                        message=f"StackSpot API error: {response.status}",
                        provider_type="stackspot",
                    )

                if kwargs.get("stream", False):
                    return self._stream_response(response)

                result = await response.json()
                return cast(str, result["choices"][0]["text"])

        except aiohttp.ClientError as e:
            raise ProviderAPIError(
                message=f"StackSpot API request failed: {e}",
                provider_type="stackspot",
            ) from e

    async def _stream_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> AsyncGenerator[str, None]:
        """Process streaming response.

        Args:
            response: The HTTP response

        Yields:
            Text chunks as they are generated

        Raises:
            ProviderAPIError: If streaming fails
        """
        try:
            async for line in response.content:
                if line:
                    chunk = line.decode("utf-8").strip()
                    if chunk and chunk != "[DONE]":
                        yield chunk

        except Exception as e:
            raise ProviderAPIError(
                message=f"StackSpot streaming failed: {e}",
                provider_type="stackspot",
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("StackSpot provider cleaned up")

    async def embed(self, text: str, **kwargs: EmbeddingKwargs) -> list[float]:
        """Generate embeddings for text using StackSpot.

        Args:
            text: Text to generate embeddings for
            **kwargs: Additional provider-specific parameters defined in EmbeddingKwargs

        Returns:
            List of embedding values

        Raises:
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self._session:
            raise ProviderInitError(
                message="StackSpot provider not initialized",
                provider_type="stackspot",
            )

        model_params = kwargs.get("model_params", {})
        payload = {
            "model": model_params.get("model", self._model),
            "input": text,
            **kwargs,
        }

        try:
            async with self._session.post(
                f"{self._base_url}/embeddings",
                json=payload,
            ) as response:
                if response.status == 429:
                    raise ProviderRateLimitError(
                        message="StackSpot rate limit exceeded",
                        provider_type="stackspot",
                    )

                if response.status != 200:
                    text = await response.text()
                    logger.warning(
                        "StackSpot API error",
                        extra={
                            "status": str(response.status),
                            "response": text,
                        },
                    )
                    raise ProviderAPIError(
                        message=f"StackSpot API error: {response.status}",
                        provider_type="stackspot",
                    )

                result = await response.json()
                return cast(list[float], result["data"][0]["embedding"])

        except aiohttp.ClientError as e:
            raise ProviderAPIError(
                message=f"StackSpot API request failed: {e}",
                provider_type="stackspot",
            ) from e

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message.

        Args:
            message: Provider message to process

        Returns:
            Provider response or async generator of responses

        Raises:
            ProviderError: If message processing fails
            ConfigurationError: If provider is not initialized
        """
        if not self._session:
            raise ProviderInitError(
                message="StackSpot provider not initialized",
                provider_type="stackspot",
            )

        # Get generation parameters from message metadata
        kwargs = message.metadata or {}
        stream = kwargs.get("stream", False)

        # Generate response
        try:
            if stream:
                response = await self.complete(str(message.content), kwargs=kwargs)
                if isinstance(response, AsyncGenerator):

                    async def stream_responses():
                        async for chunk in response:
                            yield ProviderResponse(
                                provider_id=self.id,
                                provider_type=self.type,
                                content=chunk,
                                metadata={"model": self._model},
                            )

                    return stream_responses()
            else:
                response = await self.complete(str(message.content), kwargs=kwargs)
                if isinstance(response, str):
                    return ProviderResponse(
                        provider_id=self.id,
                        provider_type=self.type,
                        content=response,
                        metadata={"model": self._model},
                    )

            raise ProviderAPIError(
                message="Invalid response type from complete method",
                provider_type="stackspot",
            )

        except Exception as e:
            raise ProviderAPIError(
                message=f"Failed to process message: {e}",
                provider_type="stackspot",
            ) from e
