"""OpenRouter provider for LLM tasks.

This module provides the OpenRouter provider implementation for LLM tasks,
supporting various models through OpenRouter's API.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from pepperpy.core.registry import Registry
from pepperpy.llm.errors import LLMConfigError, LLMError
from pepperpy.llm.provider import (
    GenerationChunk,
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.plugin.resources import ResourceType

logger = logging.getLogger(__name__)

# Default timeouts
DEFAULT_TIMEOUT = 120  # 2 minutes
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider for LLM tasks.

    This provider allows interaction with various LLM models through
    the OpenRouter API, which provides a unified interface to multiple
    model providers including OpenAI, Anthropic, and others.
    """

    def __init__(
        self, name: str = "openrouter", config: dict[str, Any] | None = None
    ) -> None:
        """Initialize the provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
        """
        super().__init__(name=name, config=config)
        self._session: aiohttp.ClientSession | None = None
        self._api_key = self.get_config("api_key")
        self._base_url = self.get_config("base_url", "https://openrouter.ai/api/v1")
        self._default_model = self.get_config("default_model", "openai/gpt-3.5-turbo")
        self._timeout = self.get_config("timeout", DEFAULT_TIMEOUT)
        self._max_retries = self.get_config("max_retries", MAX_RETRIES)

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._api_key:
            raise LLMConfigError("OpenRouter API key not configured")

        timeout = ClientTimeout(total=self._timeout)
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                "X-Title": "PepperPy",
            },
            timeout=timeout,
        )

        async def cleanup_session(session: aiohttp.ClientSession) -> None:
            if not session.closed:
                await session.close()

        await self.register_resource(ResourceType.NETWORK, "session", self._session)

        # Store cleanup function for later use
        self._cleanup_session = cleanup_session
        self.initialized = True

    def _convert_messages(self, messages: str | list[Message]) -> list[dict[str, str]]:
        """Convert messages to OpenRouter format.

        Args:
            messages: Messages to convert

        Returns:
            List of messages in OpenRouter format
        """
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]

        return [
            {
                "role": message.role.value.lower(),
                "content": message.content,
            }
            for message in messages
        ]

    async def _make_request(
        self, endpoint: str, payload: dict[str, Any], stream: bool = False
    ) -> Any:
        """Make a request to the OpenRouter API with retries.

        Args:
            endpoint: API endpoint
            payload: Request payload
            stream: Whether this is a streaming request

        Returns:
            API response

        Raises:
            LLMError: If the request fails after retries
        """
        if not self._session:
            raise LLMError("Provider not initialized")

        last_error = None
        for attempt in range(self._max_retries):
            try:
                async with self._session.post(
                    f"{self._base_url}/{endpoint}",
                    json=payload,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise LLMError(
                            f"OpenRouter API error: {response.status} - {error_text}"
                        )

                    if stream:
                        return response
                    return await response.json()

            except TimeoutError:
                last_error = LLMError(f"Request timed out after {self._timeout}s")
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{self._max_retries})"
                )

            except aiohttp.ClientError as e:
                last_error = LLMError(f"OpenRouter API request failed: {e}")
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self._max_retries}): {e}"
                )

            if attempt < self._max_retries - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        raise last_error or LLMError("Request failed after retries")

    async def generate(
        self,
        messages: str | list[Message],
        model: str | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a response.

        Args:
            messages: Messages to generate from
            model: Model to use
            **kwargs: Additional arguments to pass to the API

        Returns:
            Generation result

        Raises:
            LLMError: If an error occurs during generation
        """
        model = model or self._default_model
        converted_messages = self._convert_messages(messages)

        try:
            data = await self._make_request(
                "chat/completions",
                {
                    "model": model,
                    "messages": converted_messages,
                    **kwargs,
                },
            )

            return GenerationResult(
                content=data["choices"][0]["message"]["content"],
                messages=messages
                if isinstance(messages, list)
                else [Message(role=MessageRole.USER, content=messages)],
                metadata={
                    "model": model,
                    "provider": "openrouter",
                    "raw_response": data,
                },
            )

        except LLMError as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def stream(
        self,
        messages: str | list[Message],
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Stream a response.

        Args:
            messages: Messages to generate from
            model: Model to use
            **kwargs: Additional arguments to pass to the API

        Yields:
            Generation chunks

        Raises:
            LLMError: If an error occurs during generation
        """
        model = model or self._default_model
        converted_messages = self._convert_messages(messages)

        try:
            response = await self._make_request(
                "chat/completions",
                {
                    "model": model,
                    "messages": converted_messages,
                    "stream": True,
                    **kwargs,
                },
                stream=True,
            )

            async for line in response.content:
                line = line.strip()
                if not line or line == b"data: [DONE]":
                    continue

                if not line.startswith(b"data: "):
                    continue

                try:
                    data = line[6:].decode("utf-8")
                    chunk = json.loads(data)

                    if not chunk["choices"]:
                        continue

                    delta = chunk["choices"][0].get("delta", {})
                    if "content" not in delta:
                        continue

                    yield GenerationChunk(
                        content=delta["content"],
                        metadata={
                            "model": model,
                            "provider": "openrouter",
                            "raw_response": chunk,
                        },
                    )
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
                    logger.warning(f"Failed to parse chunk: {e}")
                    continue

        except LLMError as e:
            logger.error(f"Streaming failed: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._cleanup_session(self._session)
        await super().cleanup()


# Register the provider in the registry
Registry.register_provider("llm", "openrouter", OpenRouterProvider)
