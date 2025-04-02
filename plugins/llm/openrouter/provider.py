"""OpenRouter provider for LLM tasks.

This module provides the OpenRouter provider implementation for LLM tasks,
supporting various models through OpenRouter's API.
"""

import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Union

import aiohttp

from pepperpy.core.errors import ProviderError
from pepperpy.llm import (
    GenerationChunk,
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.plugins.plugin import PepperpyPlugin


class OpenRouterProvider(LLMProvider, PepperpyPlugin):
    """OpenRouter provider for LLM tasks."""

    plugin_type = "llm"
    provider_type = "openrouter"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider."""
        super().__init__(**kwargs)
        self._session: Optional[aiohttp.ClientSession] = None

        # Set base URL and defaults
        self._base_url = "https://openrouter.ai/api/v1/"
        self._model = kwargs.get("model", "openai/gpt-4o-mini")
        self._temperature = kwargs.get("temperature", 0.7)
        self._max_tokens = kwargs.get("max_tokens", 1000)

        # Get API key from plugin config (busca automaticamente nas variáveis de ambiente)
        api_key = self.get_config("api_key") or self.get_config("openrouter_api_key")

        if not api_key:
            raise ProviderError("API key is required for OpenRouter provider.")

        # Remove Bearer prefix if present and strip whitespace
        self._api_key: str = str(api_key).replace("Bearer ", "").strip()

    @property
    def api_key(self) -> str:
        """Get API key."""
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set API key."""
        # Remove Bearer prefix if present
        self._api_key = value.replace("Bearer ", "").strip()

    @property
    def model(self) -> str:
        """Get model name."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set model name."""
        self._model = value

    @property
    def temperature(self) -> float:
        """Get temperature."""
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        """Set temperature."""
        self._temperature = value

    @property
    def max_tokens(self) -> int:
        """Get max tokens."""
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        """Set max tokens."""
        self._max_tokens = value

    async def initialize(self) -> None:
        """Initialize the provider by creating a session."""
        if not self._api_key:
            raise ProviderError("API key is required for OpenRouter provider")

        if self._session is None:
            # Create session with default headers
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                "X-Title": "PepperPy",
                "Content-Type": "application/json",
            }

            self._session = aiohttp.ClientSession(headers=headers)

    def _convert_messages(
        self, messages: Union[str, List[Message]]
    ) -> List[Dict[str, Any]]:
        """Convert PepperPy messages to OpenRouter format."""
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]

        openrouter_messages = []
        for msg in messages:
            message_dict = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                message_dict["name"] = msg.name

            openrouter_messages.append(message_dict)

        return openrouter_messages

    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text using the OpenRouter API."""
        if not self._session:
            await self.initialize()
            assert self._session is not None

        # Convert messages to OpenRouter format
        openrouter_messages = self._convert_messages(messages)

        # Use auto-bound attributes with kwargs overrides
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        model = kwargs.get("model", self._model)

        request_data = {
            "model": model,
            "messages": openrouter_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with self._session.post(
                f"{self._base_url}chat/completions",
                json=request_data,
            ) as response:
                if response.status == 401:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    raise ProviderError(
                        f"OpenRouter API authentication failed: {error_msg}"
                    )
                elif response.status == 402:
                    error_data = await response.json()
                    raise ProviderError(
                        f"OpenRouter API payment required: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    )
                elif response.status != 200:
                    error_data = await response.json()
                    raise ProviderError(
                        f"OpenRouter API request failed with status {response.status}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    )

                data = await response.json()

                # Extract response content
                content = data["choices"][0]["message"]["content"]

                # Build message history
                if isinstance(messages, str):
                    messages_list = [Message(role=MessageRole.USER, content=messages)]
                else:
                    messages_list = messages.copy()

                # Add response to messages
                messages_list.append(
                    Message(role=MessageRole.ASSISTANT, content=content)
                )

                return GenerationResult(
                    content=content,
                    messages=messages_list,
                    usage=data.get("usage"),
                    metadata={
                        "model": data.get("model"),
                        "created": data.get("created"),
                        "id": data.get("id"),
                    },
                )

        except aiohttp.ClientError as e:
            raise ProviderError(f"OpenRouter API error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}") from e

    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Stream chat completion from the model.

        Args:
            messages: Messages to generate from
            **kwargs: Additional parameters for generation

        Yields:
            Generated content chunks

        Raises:
            ProviderError: If API request fails
        """
        if not self._session:
            await self.initialize()
            assert self._session is not None

        # Convert messages to OpenRouter format
        openrouter_messages = self._convert_messages(messages)

        # Use auto-bound attributes with kwargs overrides
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        model = kwargs.get("model", self._model)

        try:
            async with self._session.post(
                f"{self._base_url}chat/completions",
                json={
                    "model": model,
                    "messages": openrouter_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise ProviderError(
                        f"OpenRouter API stream request failed with status {response.status}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    )

                # Stream the response
                async for line in response.content:
                    line = line.strip()
                    if not line or line == b"data: [DONE]":
                        continue

                    if line.startswith(b"data: "):
                        try:
                            data = json.loads(line[6:])
                            if not data.get("choices"):
                                continue

                            choice = data["choices"][0]
                            if not choice.get("delta") or not choice["delta"].get(
                                "content"
                            ):
                                continue

                            content = choice["delta"]["content"]
                            yield GenerationChunk(content=content)
                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            raise ProviderError(
                                f"Failed to parse streaming response: {e}"
                            ) from e

        except aiohttp.ClientError as e:
            raise ProviderError(f"OpenRouter API streaming error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected streaming error: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None
