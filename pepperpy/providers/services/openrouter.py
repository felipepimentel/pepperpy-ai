"""OpenRouter provider implementation for the Pepperpy framework.

This module implements the OpenRouter provider, supporting chat completions and
embeddings using OpenRouter's API. It handles streaming responses, rate limiting,
and proper error propagation. OpenRouter provides access to multiple AI models
through a single API.

Example:
    ```python
    config = ProviderConfig(
        provider_type="openrouter",
        api_key="your-api-key",
        model="your-chosen-model"
    )
    provider = OpenRouterProvider(config)
    await provider.initialize()
    response = await provider.complete("Hello, how are you?")
    print(response)
    ```
"""

# Standard library imports
import json
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

# Third-party imports
import aiohttp
from aiohttp import ClientSession, ClientTimeout

# Local imports
from pepperpy.monitoring import logger

from ..domain import (
    ProviderAPIError,
    ProviderError,
    ProviderInitError,
    ProviderRateLimitError,
)
from ..provider import Provider, ProviderConfig

# Type aliases
JsonDict = dict[str, Any]


class OpenRouterProvider(Provider):
    """Provider implementation for OpenRouter AI API.

    This provider implements the Provider protocol for OpenRouter's API, supporting:
    - Chat completions with GPT-4 and other models
    - Streaming responses
    - Rate limit handling
    - Proper error propagation

    Attributes:
        config (ProviderConfig): The provider configuration
        BASE_URL (str): OpenRouter API base URL
    """

    BASE_URL: str = "https://api.openrouter.ai/api/v1"

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the OpenRouter provider.

        Args:
            config: Provider configuration containing API key and other settings

        Note:
            The provider is not ready for use until initialize() is called.
        """
        super().__init__(config)
        self._session: ClientSession | None = None
        self._model: str = config.model or "anthropic/claude-3-opus-20240229"
        self._timeout: ClientTimeout = ClientTimeout(total=config.timeout)

    async def initialize(self) -> None:
        """Initialize the OpenRouter client.

        This method sets up the aiohttp session with the required headers
        and authentication for OpenRouter's API.

        Raises:
            ProviderInitError: If initialization fails
        """
        try:
            self._session = ClientSession(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "Pepperpy Framework",
                },
            )
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize OpenRouter provider: {e!s}",
                provider_type="openrouter",
                details={"error": str(e)},
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources by closing the aiohttp session."""
        if self._session:
            await self._session.close()

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

        try:
            if stream:

                async def response_generator() -> AsyncGenerator[str, None]:
                    session = self._session
                    if not session:
                        raise ProviderError(
                            "Session lost during streaming",
                            provider_type=self.config.provider_type,
                        )

                    async with session.post(
                        f"{self.BASE_URL}/chat/completions",
                        json=payload,
                        raise_for_status=False,
                    ) as response:
                        if response.status != 200:
                            error_data = await response.json()
                            raise ProviderError(
                                "OpenRouter API error: "
                                f"{error_data.get('error', 'Unknown error')}",
                                provider_type=self.config.provider_type,
                                details=error_data,
                            )

                        async for line in response.content:
                            if not line:
                                continue

                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                data = line_str[6:]
                                if data == "[DONE]":
                                    break

                                try:
                                    chunk = json.loads(data)
                                    if content := chunk["choices"][0]["delta"].get(
                                        "content"
                                    ):
                                        yield content
                                except json.JSONDecodeError:
                                    logger.warning(
                                        "Failed to decode streaming response",
                                        extra={"data": data},
                                    )
                                    continue

                return response_generator()

            session = self._session
            if not session:
                raise ProviderError(
                    "Session lost during request",
                    provider_type=self.config.provider_type,
                )

            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                raise_for_status=False,
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise ProviderError(
                        "OpenRouter API error: "
                        f"{error_data.get('error', 'Unknown error')}",
                        provider_type=self.config.provider_type,
                        details=error_data,
                    )

                data = await response.json()
                if not isinstance(data, dict):
                    raise ProviderError(
                        "Invalid response format",
                        provider_type=self.config.provider_type,
                        details={"response": data},
                    )
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if not isinstance(content, str):
                    raise ProviderError(
                        "Invalid response content",
                        provider_type=self.config.provider_type,
                        details={"content": content},
                    )
                return content

        except Exception as e:
            raise ProviderError(
                f"Failed to complete prompt: {e!s}",
                provider_type=self.config.provider_type,
                details={"error": str(e)},
            ) from e

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text using OpenRouter.

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
                model="openai/text-embedding-ada-002"
            )
            ```
        """
        if not self._session:
            raise ProviderInitError(
                "OpenRouter provider not initialized", provider_type="openrouter"
            )

        payload: JsonDict = {
            "model": kwargs.get("model", "openai/text-embedding-ada-002"),
            "input": text,
        }

        try:
            async with self._session.post(
                f"{self.BASE_URL}/embeddings", json=payload, raise_for_status=False
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise ProviderAPIError(
                        "OpenRouter API error: "
                        f"{error_data.get('error', 'Unknown error')}",
                        provider_type="openrouter",
                        details=error_data,
                    )

                data = await response.json()
                embeddings: list[float] = data["data"][0]["embedding"]
                return embeddings

        except ProviderRateLimitError:
            raise
        except Exception as e:
            raise ProviderAPIError(
                f"OpenRouter embedding error: {e!s}",
                provider_type="openrouter",
                details={"error": str(e)},
            ) from e

    async def _stream_response(self, payload: JsonDict) -> AsyncIterator[str]:
        """Stream response from OpenRouter.

        Args:
            payload: Request payload containing model, messages, and other parameters

        Yields:
            Text chunks as they are generated by the model

        Raises:
            ProviderInitError: If session is not initialized
            ProviderAPIError: If the API call fails
            ProviderRateLimitError: If rate limit is exceeded
        """
        if not self._session:
            raise ProviderInitError(
                "OpenRouter provider not initialized", provider_type="openrouter"
            )

        payload["stream"] = True

        try:
            async with self._session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                raise_for_status=False,
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise ProviderAPIError(
                        "OpenRouter API error: "
                        f"{error_data.get('error', 'Unknown error')}",
                        provider_type="openrouter",
                        details=error_data,
                    )

                async for line_bytes in response.content.iter_any():
                    line = line_bytes.decode("utf-8").strip()
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if content := chunk["choices"][0]["delta"].get("content"):
                                yield content
                        except json.JSONDecodeError:
                            logger.warning(
                                "Failed to decode streaming response", data=data
                            )
                            continue

        except ProviderRateLimitError:
            raise
        except Exception as e:
            raise ProviderAPIError(
                f"OpenRouter streaming error: {e!s}",
                provider_type="openrouter",
                details={"error": str(e)},
            ) from e
