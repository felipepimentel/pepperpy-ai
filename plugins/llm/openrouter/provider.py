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
    """OpenRouter provider for LLM tasks.

    This provider allows interaction with various LLM models through
    the OpenRouter API, which provides a unified interface to multiple
    model providers including OpenAI, Anthropic, and others.
    """

    plugin_type = "llm"
    provider_type = "openrouter"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider with configuration.

        Args:
            **kwargs: Configuration parameters including:
                - api_key: OpenRouter API key
                - model: Model name (default: openai/gpt-4o-mini)
                - temperature: Generation temperature (default: 0.7)
                - max_tokens: Maximum tokens to generate (default: 1000)

        Raises:
            ProviderError: If API key is not provided
        """
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
        """Get API key.

        Returns:
            The configured API key
        """
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Set API key.

        Args:
            value: The API key to set
        """
        # Remove Bearer prefix if present
        self._api_key = value.replace("Bearer ", "").strip()

    @property
    def model(self) -> str:
        """Get model name.

        Returns:
            The configured model name
        """
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Set model name.

        Args:
            value: The model name to set
        """
        self._model = value

    @property
    def temperature(self) -> float:
        """Get temperature.

        Returns:
            The configured temperature value
        """
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        """Set temperature.

        Args:
            value: The temperature value to set
        """
        self._temperature = value

    @property
    def max_tokens(self) -> int:
        """Get max tokens.

        Returns:
            The configured maximum tokens value
        """
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        """Set max tokens.

        Args:
            value: The maximum tokens value to set
        """
        self._max_tokens = value

    async def initialize(self) -> None:
        """Initialize the provider by creating a session.

        This method sets up the HTTP session with proper authentication headers.

        Raises:
            ProviderError: If API key is not available
        """
        if self.initialized:
            return

        if not self._api_key:
            raise ProviderError("API key is required for OpenRouter provider")

        # Create session with default headers
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://github.com/pimentel/pepperpy",
            "X-Title": "PepperPy",
            "Content-Type": "application/json",
        }

        self._session = aiohttp.ClientSession(headers=headers)

        # Register session for automatic cleanup
        self.register_resource("session", self._session)

        # Mark as initialized
        self.initialized = True

    def _convert_messages(
        self, messages: Union[str, List[Message]]
    ) -> List[Dict[str, Any]]:
        """Convert PepperPy messages to OpenRouter format.

        Args:
            messages: String prompt or list of Message objects

        Returns:
            List of message dictionaries in OpenRouter format
        """
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
        """Generate text using the OpenRouter API.

        Args:
            messages: String prompt or list of Message objects
            **kwargs: Additional parameters including:
                - temperature: Generation temperature
                - max_tokens: Maximum tokens to generate
                - model: Model name to use

        Returns:
            Generation result containing the model's response

        Raises:
            ProviderError: If API request fails or returns an error
        """
        if not self.initialized:
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
            raise ProviderError(f"OpenRouter API connection error: {e}") from e
        except json.JSONDecodeError as e:
            raise ProviderError(f"OpenRouter API returned invalid JSON: {e}") from e
        except KeyError as e:
            raise ProviderError(
                f"OpenRouter API returned unexpected response format: missing {e}"
            ) from e
        except Exception as e:
            raise ProviderError(f"Unexpected error during API call: {e}") from e

    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Stream chat completion from the model.

        Args:
            messages: String prompt or list of Message objects
            **kwargs: Additional parameters including:
                - temperature: Generation temperature
                - max_tokens: Maximum tokens to generate
                - model: Model name to use

        Yields:
            Generated content chunks

        Raises:
            ProviderError: If API request fails or returns an error
        """
        if not self.initialized:
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
            "stream": True,
        }

        try:
            async with self._session.post(
                f"{self._base_url}chat/completions",
                json=request_data,
            ) as response:
                if response.status != 200:
                    try:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get(
                            "message", "Unknown error"
                        )
                    except:
                        error_msg = await response.text()
                    raise ProviderError(
                        f"OpenRouter API request failed with status {response.status}: {error_msg}"
                    )

                # Process SSE stream
                buffer = ""
                async for line in response.content:
                    line = line.decode("utf-8")
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(data)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield GenerationChunk(
                                    content=content,
                                    metadata={
                                        "model": chunk_data.get("model"),
                                        "created": chunk_data.get("created"),
                                        "id": chunk_data.get("id"),
                                    },
                                )
                        except json.JSONDecodeError:
                            buffer += data
                            try:
                                chunk_data = json.loads(buffer)
                                buffer = ""
                                delta = chunk_data.get("choices", [{}])[0].get(
                                    "delta", {}
                                )
                                content = delta.get("content", "")
                                if content:
                                    yield GenerationChunk(
                                        content=content,
                                        metadata={
                                            "model": chunk_data.get("model"),
                                            "created": chunk_data.get("created"),
                                            "id": chunk_data.get("id"),
                                        },
                                    )
                            except json.JSONDecodeError:
                                # Continue buffering
                                pass

        except aiohttp.ClientError as e:
            raise ProviderError(
                f"OpenRouter API connection error during streaming: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise ProviderError(
                f"OpenRouter API returned invalid JSON during streaming: {e}"
            ) from e
        except KeyError as e:
            raise ProviderError(
                f"OpenRouter API returned unexpected response format during streaming: missing {e}"
            ) from e
        except Exception as e:
            raise ProviderError(f"Unexpected streaming error: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources.
        
        This automatically cleans up the HTTP session and other resources.
        """
        try:
            # Fechar explicitamente a sessão HTTP se existir
            if self._session and not self._session.closed:
                try:
                    await self._session.close()
                    self._session = None
                    self.logger.debug("Closed OpenRouter HTTP session")
                except Exception as e:
                    self.logger.error(f"Error closing OpenRouter HTTP session: {e}")
        finally:
            # ResourceMixin will handle cleanup of other registered resources
            await super().cleanup()
            self.initialized = False
