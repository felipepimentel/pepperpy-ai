"""OpenRouter provider implementation for LLM capabilities.

This module provides an OpenRouter-based implementation of the LLM provider interface,
supporting various models through OpenRouter's API.

Example:
    >>> from pepperpy.llm import LLMProvider
    >>> provider = LLMProvider.from_config({
    ...     "provider": "openrouter",
    ...     "model": "openai/gpt-3.5-turbo",
    ...     "api_key": "sk-or-..."
    ... })
    >>> messages = [
    ...     Message(role="system", content="You are helpful."),
    ...     Message(role="user", content="What's the weather?")
    ... ]
    >>> result = await provider.generate(messages)
    >>> print(result.content)
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import httpx

from pepperpy.llm.base import (
    GenerationChunk,
    GenerationResult,
    LLMError,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.core.utils.imports import lazy_provider_class, import_provider

logger = logging.getLogger(__name__)

@lazy_provider_class('llm', 'openrouter')
class OpenRouterProvider(LLMProvider):
    """OpenRouter implementation of the LLM provider interface.

    This provider supports:
    - Various models through OpenRouter's API
    - Chat-based interactions
    - Streaming responses
    """

    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-3.5-turbo",
        **kwargs: Any
    ) -> None:
        """Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        # Import openrouter only when provider is instantiated
        openrouter = import_provider('openrouter', 'llm', 'openrouter')
        
        self._api_key = api_key or self._get_api_key()
        self.model = model
        self.client = openrouter.OpenRouter(api_key=self._api_key)
        self._client: Optional[httpx.AsyncClient] = None
        self._config = {
            "provider": "openrouter",
            "api_key": self._api_key,
            "model": self.model
        }

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return self._config

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities including:
            - supported_models: List of supported models
            - max_tokens: Maximum tokens per request
            - supports_streaming: Whether streaming is supported
            - supports_embeddings: Whether embeddings are supported
            - additional provider-specific capabilities
        """
        return {
            "embeddings": False,
            "streaming": True,
            "chat_based": True,
            "function_calling": False,
            "supported_models": [
                "anthropic/claude-3-sonnet",
                "anthropic/claude-3-opus",
                "anthropic/claude-2",
                "openai/gpt-4",
                "openai/gpt-3.5-turbo",
                "google/palm-2",
                "meta/llama-2-70b-chat",
                "meta/llama-2-13b-chat",
                "meta/llama-2-7b-chat"
            ]
        }

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._api_key

    def _get_api_key(self) -> str:
        """Get API key from environment."""
        import os
        
        api_key = os.environ.get("PEPPERPY_LLM__OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key not found. Set PEPPERPY_LLM__OPENROUTER_API_KEY "
                "environment variable or pass api_key to constructor."
            )
        return api_key

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url="https://openrouter.ai/api/v1",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy Framework",
                }
            )

    async def cleanup(self) -> None:
        """Cleanup OpenRouter clients."""
        try:
            if self._client:
                await self._client.aclose()
        except Exception as e:
            logger.warning(f"Error closing client: {e}")
        finally:
            self._client = None

        await super().cleanup()

    def _convert_messages(
        self, messages: Union[str, List[Message]]
    ) -> List[dict]:
        """Convert messages to OpenRouter format.

        Args:
            messages: String prompt or list of messages

        Returns:
            List of messages in OpenRouter format

        Raises:
            ValidationError: If messages are invalid
        """
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]

        openrouter_messages = []
        for msg in messages:
            if not isinstance(msg, Message):
                raise LLMError(f"Invalid message type: {type(msg)}")

            message_dict = {
                "role": msg.role if isinstance(msg.role, str) else msg.role.value,
                "content": msg.content,
            }
            if hasattr(msg, "name") and msg.name:
                message_dict["name"] = msg.name

            openrouter_messages.append(message_dict)

        return openrouter_messages

    def _create_generation_result(
        self,
        completion: dict,
        messages: List[dict],
    ) -> GenerationResult:
        """Create a GenerationResult from OpenRouter completion.

        Args:
            completion: OpenRouter chat completion
            messages: Original messages in OpenRouter format

        Returns:
            GenerationResult with completion details
        """
        content = completion["choices"][0]["message"]["content"]
        if content is None:
            content = ""

        return GenerationResult(
            content=content,
            messages=[
                Message(
                    role=msg["role"],
                    content=str(msg.get("content", "")),
                    name=msg.get("name"),
                )
                for msg in messages
            ],
            usage=completion["usage"]["model_dump"] if completion["usage"] else None,
            metadata={
                "model": completion["model"],
                "created": completion["created"],
                "id": completion["id"],
            },
        )

    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text based on input messages.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """
        if not self._client:
            raise RuntimeError("Provider not initialized")

        try:
            openrouter_messages = self._convert_messages(messages)
            response = await self._client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": openrouter_messages
                }
            )
            response.raise_for_status()
            data = response.json()

            return self._create_generation_result(data, openrouter_messages)
        except Exception as e:
            raise LLMError(f"OpenRouter generation failed: {e}")

    async def chat(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response in a chat context.
        
        Args:
            messages: List of messages in the chat history.
                Each message should have 'role' and 'content' keys.
            
        Returns:
            The generated response.
            
        Raises:
            RuntimeError: If the provider is not initialized.
            httpx.HTTPError: If the API request fails.
        """
        if not self._client:
            raise RuntimeError("Provider not initialized")

        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages
            }
        )
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def stream(
        self, messages: Union[str, List[Message]], **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text using OpenRouter's streaming chat completion API.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options
                - temperature: Sampling temperature (0-2)
                - max_tokens: Maximum tokens to generate
                - stop: List of stop sequences
                - presence_penalty: Presence penalty (-2 to 2)
                - frequency_penalty: Frequency penalty (-2 to 2)

        Returns:
            AsyncIterator yielding GenerationChunk objects

        Raises:
            LLMError: If generation fails
        """
        if not self._client:
            raise RuntimeError("OpenRouter client not initialized")

        try:
            openrouter_messages = self._convert_messages(messages)
            stream = await self._client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": openrouter_messages,
                    "stream": True,
                },
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy Framework",
                }
            )

            async for chunk in stream:
                if chunk["choices"][0]["delta"]["content"]:
                    yield GenerationChunk(
                        content=chunk["choices"][0]["delta"]["content"],
                        finish_reason=chunk["choices"][0]["finish_reason"],
                        metadata={
                            "model": chunk["model"],
                            "created": chunk["created"],
                            "id": chunk["id"],
                        },
                    )

        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            raise LLMError(f"OpenRouter streaming failed: {e}")
