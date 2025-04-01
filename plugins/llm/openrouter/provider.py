"""OpenRouter provider for LLM tasks.

This module provides the OpenRouter provider implementation for LLM tasks,
supporting various models through OpenRouter's API.
"""

import asyncio
import json
import os
from collections.abc import AsyncIterator, AsyncGenerator
from typing import Any, Dict, List, Optional, TypeVar, Union

import httpx
import aiohttp

from pepperpy.llm import (
    GenerationChunk,
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.plugins import ProviderPlugin
from pepperpy.core.errors import ProviderError
from pepperpy.plugins.plugin import PepperpyPlugin

T = TypeVar("T", bound="OpenRouterProvider")


class OpenRouterProvider(LLMProvider, ProviderPlugin, PepperpyPlugin):
    """OpenRouter provider for LLM tasks."""

    # These attributes will be auto-bound from plugin.yaml with fallback defaults
    api_key: str = ""  # Will be filled by framework from env vars
    model: str = "openai/gpt-3.5-turbo"
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.7
    max_tokens: int = 1024
    client: Optional[httpx.AsyncClient] = None
    _test_mode: bool = False
    _session: Optional[aiohttp.ClientSession] = None
    _initialized: bool = False

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the OpenRouter provider."""
        super().__init__(**kwargs)
        self.client = None
        self._api_key = str(kwargs.get("api_key", ""))
        self._model = str(kwargs.get("model", "openai/gpt-3.5-turbo"))
        self._temperature = float(kwargs.get("temperature", 0.7))
        self._max_tokens = int(kwargs.get("max_tokens", 1024))

        # Ensure we set the API key if provided in kwargs
        if "api_key" in kwargs:
            self.api_key = kwargs["api_key"]

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._api_key = value

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        self._temperature = value

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        self._max_tokens = value

    @property
    def initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    @classmethod
    def from_config(cls, **config: Any) -> "OpenRouterProvider":
        """Create an instance from configuration.

        Args:
            **config: Configuration parameters

        Returns:
            OpenRouterProvider instance
        """
        print(
            f"DEBUG: OpenRouterProvider.from_config called with config: {list(config.keys())}"
        )

        instance = cls()

        # Base URL
        if "base_url" in config:
            instance.base_url = config["base_url"]

        # Model
        if "model" in config:
            instance.model = config["model"]

        # Temperature
        if "temperature" in config:
            instance.temperature = float(config["temperature"])

        # Max tokens
        if "max_tokens" in config:
            instance.max_tokens = int(config["max_tokens"])

        # API key - check both the original api_key and our provider-prefixed key
        if "api_key" in config:
            print("DEBUG: Found api_key in config")
            instance.api_key = config["api_key"]
        elif "openrouter_api_key" in config:
            print("DEBUG: Found openrouter_api_key in config")
            instance.api_key = config["openrouter_api_key"]
        else:
            print("DEBUG: No API key found in config!")

        return instance

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the OpenRouter client."""
        if self.initialized:
            return

        if config:
            self._api_key = str(config.get("api_key", self._api_key))
            self._model = str(config.get("model", self._model))
            self._temperature = float(config.get("temperature", self._temperature))
            self._max_tokens = int(config.get("max_tokens", self._max_tokens))

        if not self.api_key:
            raise ProviderError("API key is required for OpenRouter provider")

        print(
            f"DEBUG: Initializing OpenRouter with API key: {self.api_key[:5]}...{self.api_key[-5:]}"
        )
        self._test_mode = False

        self._session = aiohttp.ClientSession()
        self._initialized = True

    def _convert_messages(
        self, messages: Union[str, List[Message]]
    ) -> List[Dict[str, Any]]:
        """Convert PepperPy messages to OpenRouter format."""
        # Handle single string as user message
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]

        # Convert list of Message objects
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
        # Convert messages to OpenRouter format
        openrouter_messages = self._convert_messages(messages)

        # Use auto-bound attributes with kwargs overrides
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        model = kwargs.get("model", self.model)

        # Se estamos em modo de teste, simular uma resposta
        if self._test_mode:
            print(
                "DEBUG: Using test mode for OpenRouter provider. Returning simulated response."
            )

            # Create a simulated response
            content = "This is a simulated response from the OpenRouter provider in test mode."

            # If there's a prompt/question in the messages, craft a more specific response
            for msg in openrouter_messages:
                if msg["role"] == "user":
                    if (
                        "hello" in msg["content"].lower()
                        or "hi" in msg["content"].lower()
                    ):
                        content = "Hello! How can I assist you today?"
                    elif "help" in msg["content"].lower():
                        content = "I'm here to help. What do you need assistance with?"
                    elif (
                        "write" in msg["content"].lower()
                        and "poem" in msg["content"].lower()
                    ):
                        content = "Roses are red,\nViolets are blue,\nThis is test mode,\nJust for you."
                    elif "haiku" in msg["content"].lower():
                        content = "Artificial mind / Learning, growing, evolving / Future now defined."

            # Build result
            if isinstance(messages, str):
                messages_list = [Message(role=MessageRole.USER, content=messages)]
            else:
                messages_list = messages.copy()

            # Add response to messages
            messages_list.append(Message(role=MessageRole.ASSISTANT, content=content))

            return GenerationResult(
                content=content,
                messages=messages_list,
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
                metadata={"model": "test-model", "created": 0, "id": "test-id"},
            )

        # Make API call
        if not self._session:
            await self.initialize()
            assert self._session is not None

        try:
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": openrouter_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy",
                },
            ) as response:
                data = await response.json()
                if response.status != 200:
                    error_msg = data.get("error", {}).get("message", str(data))
                    raise ProviderError(f"OpenRouter API error: {error_msg}")

                if not data.get("choices") or not data["choices"][0].get(
                    "message", {}
                ).get("content"):
                    raise ProviderError("Invalid response format from OpenRouter API")

                content = data["choices"][0]["message"]["content"] or ""

                # Build result
                if isinstance(messages, str):
                    messages_list = [Message(role=MessageRole.USER, content=messages)]
                else:
                    messages_list = messages.copy()

                # Add response to messages
                messages_list.append(Message(role=MessageRole.ASSISTANT, content=content))

                # Extract usage statistics
                usage = data.get("usage")

                return GenerationResult(
                    content=content,
                    messages=messages_list,
                    usage=usage,
                    metadata={
                        "model": data.get("model"),
                        "created": data.get("created"),
                        "id": data.get("id"),
                    },
                )
        except aiohttp.ClientError as e:
            raise ProviderError(f"HTTP error: {e}")
        except json.JSONDecodeError as e:
            raise ProviderError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise ProviderError(f"OpenRouter API error: {e}")

    async def generate_stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in streaming mode using the OpenRouter API."""
        # Convert messages to OpenRouter format
        openrouter_messages = self._convert_messages(messages)

        # Use auto-bound attributes with kwargs overrides
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        model = kwargs.get("model", self.model)

        # Se estamos em modo de teste, simular uma resposta em streaming
        if self._test_mode:
            print(
                "DEBUG: Using test mode for OpenRouter provider. Returning simulated streaming response."
            )

            # Create a simulated streaming response
            content = "This is a simulated response from the OpenRouter provider in test mode."

            # If there's a prompt/question in the messages, craft a more specific response
            for msg in openrouter_messages:
                if msg["role"] == "user":
                    if (
                        "hello" in msg["content"].lower()
                        or "hi" in msg["content"].lower()
                    ):
                        content = "Hello! How can I assist you today?"
                    elif "help" in msg["content"].lower():
                        content = "I'm here to help. What do you need assistance with?"
                    elif (
                        "write" in msg["content"].lower()
                        and "poem" in msg["content"].lower()
                    ):
                        content = "Roses are red,\nViolets are blue,\nThis is test mode,\nJust for you."
                    elif "haiku" in msg["content"].lower():
                        content = "Artificial mind / Learning, growing, evolving / Future now defined."

            # Emit in short pieces to simulate streaming
            words = content.split()
            for i in range(0, len(words), 2):
                chunk_text = " ".join(words[i : i + 2]) + " "
                yield GenerationChunk(
                    content=chunk_text,
                    finish_reason=None if i < len(words) - 2 else "stop",
                    metadata={"model": "test-model"},
                )
                await asyncio.sleep(0.1)  # Simulate network delay

            # If we didn't return any chunks (empty message), still return something
            if not words:
                yield GenerationChunk(
                    content="",
                    finish_reason="stop",
                    metadata={"model": "test-model"},
                )

            return

        # Make API call with streaming
        if not self._session:
            await self.initialize()
            assert self._session is not None

        try:
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": openrouter_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy",
                },
            ) as response:
                if response.status != 200:
                    data = await response.json()
                    error_msg = data.get("error", {}).get("message", str(data))
                    raise ProviderError(f"OpenRouter API error: {error_msg}")

                # Process the streaming response
                async for line in response.content:
                    line = line.decode("utf-8").strip()

                    # Skip empty lines or non-data lines
                    if not line or line == "data: [DONE]":
                        continue

                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        try:
                            chunk = json.loads(data)

                            if not chunk.get("choices"):
                                continue

                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                yield GenerationChunk(
                                    content=content,
                                    finish_reason=chunk["choices"][0].get("finish_reason"),
                                    metadata={"model": model},
                                )
                        except Exception:
                            # Skip invalid chunks
                            continue
        except aiohttp.ClientError as e:
            raise ProviderError(f"HTTP error: {e}")
        except Exception as e:
            raise ProviderError(f"OpenRouter API error: {e}")

    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in a streaming fashion (alias for generate_stream).

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            AsyncIterator yielding GenerationChunk objects

        Raises:
            RuntimeError: If generation fails
        """
        async for chunk in self.generate_stream(messages, **kwargs):
            yield chunk

    async def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate text from messages with streaming.

        Args:
            messages: List of messages
            model: Optional model to use
            temperature: Optional temperature
            max_tokens: Optional max tokens
            **kwargs: Additional arguments

        Yields:
            Generated text chunks

        Raises:
            ProviderError: If API call fails
        """
        if not self._session:
            raise ProviderError("Provider not initialized")

        try:
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model or self.model,
                    "messages": [
                        {
                            "role": msg.role.value
                            if isinstance(msg.role, MessageRole)
                            else msg.role,
                            "content": msg.content,
                            **({"name": msg.name} if msg.name else {}),
                        }
                        for msg in messages
                    ],
                    "temperature": temperature or self.temperature,
                    "max_tokens": max_tokens or self.max_tokens,
                    "stream": True,
                    **kwargs,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy",
                },
            ) as response:
                if response.status != 200:
                    data = await response.json()
                    error_msg = data.get("error", {}).get("message", str(data))
                    raise ProviderError(f"OpenRouter API error: {error_msg}")

                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line:
                        if line.startswith("data: "):
                            line = line[6:]
                        if line == "[DONE]":
                            break
                        try:
                            data = json.loads(line)
                            if data.get("choices"):
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except aiohttp.ClientError as e:
            raise ProviderError(f"HTTP error: {e}")
        except Exception as e:
            raise ProviderError(f"OpenRouter API error: {e}")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._session:
            await self._session.close()
            self._session = None
            self._initialized = False
