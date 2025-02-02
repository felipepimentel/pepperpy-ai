"""OpenRouter provider implementation for Pepperpy.

This module provides integration with OpenRouter's API for accessing
various language models through a unified interface.
"""

from collections.abc import AsyncGenerator

import httpx

from pepperpy.monitoring import logger
from pepperpy.providers.domain import ProviderAPIError
from pepperpy.providers.provider import BaseProvider, ProviderConfig


class OpenRouterProvider(BaseProvider):
    """Provider implementation for OpenRouter.

    This provider allows access to various language models through
    OpenRouter's unified API.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the OpenRouter provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates the HTTP client and validates configuration.
        """
        self._client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            timeout=self.config.timeout,
        )

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using OpenRouter.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            Either a string response or an async generator for streaming

        Raises:
            ProviderAPIError: If the API call fails
        """
        if not self._client:
            raise ProviderAPIError("Provider not initialized")

        headers = {
            "Authorization": f"Bearer {self.config.api_key.get_secret_value()}",
            "HTTP-Referer": "https://github.com/pimentel/pepperpy",
        }

        data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": stream,
        }

        try:
            response = await self._client.post(
                "/chat/completions",
                headers=headers,
                json=data,
            )
            response.raise_for_status()

            if stream:
                return self._stream_response(response)
            else:
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(
                "OpenRouter API error",
                error=str(e),
                status_code=getattr(e.response, "status_code", None),
            )
            raise ProviderAPIError(f"OpenRouter API error: {e}")

    async def _stream_response(
        self,
        response: httpx.Response,
    ) -> AsyncGenerator[str, None]:
        """Stream the response from OpenRouter.

        Args:
            response: The streaming response

        Yields:
            Text chunks as they are generated
        """
        async for line in response.aiter_lines():
            if not line or line.startswith("data: [DONE]"):
                continue

            if not line.startswith("data: "):
                continue

            try:
                data = line[6:]  # Remove "data: " prefix
                chunk = data["choices"][0]["delta"]["content"]
                if chunk:
                    yield chunk
            except Exception as e:
                logger.error("Error parsing stream chunk", error=str(e))
                continue
