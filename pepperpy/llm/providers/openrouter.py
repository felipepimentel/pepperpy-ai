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

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from pepperpy.llm.base import (
    GenerationChunk,
    GenerationResult,
    LLMError,
    LLMProvider,
    Message,
)

logger = logging.getLogger(__name__)


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
        api_key: str,
        model: str = "openai/gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model to use for text generation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            config: Optional configuration dictionary
        """
        # Initialize LLM provider
        config = config or {}
        config["api_key"] = api_key
        config["model"] = model
        config["temperature"] = temperature
        if max_tokens is not None:
            config["max_tokens"] = max_tokens

        super().__init__(config=config)

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize OpenRouter clients."""
        await super().initialize()
        await self._initialize_clients()

    async def cleanup(self) -> None:
        """Cleanup OpenRouter clients."""
        try:
            if self._sync_client:
                await self._sync_client.close()
        except Exception as e:
            logger.warning(f"Error closing sync client: {e}")
        finally:
            self._sync_client = None

        try:
            if self._async_client:
                await self._async_client.close()
        except Exception as e:
            logger.warning(f"Error closing async client: {e}")
        finally:
            self._async_client = None

        await super().cleanup()

    async def _initialize_clients(self) -> None:
        """Initialize OpenRouter clients."""
        if not self._sync_client:
            self._sync_client = OpenAI(
                api_key=self._api_key,
                base_url=self.base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy Framework",
                },
            )
        if not self._async_client:
            self._async_client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self.base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "PepperPy Framework",
                },
            )

    def _convert_messages(
        self, messages: Union[str, List[Message]]
    ) -> List[ChatCompletionMessageParam]:
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
                "role": msg.role.value,
                "content": msg.content,
            }
            if hasattr(msg, "name") and msg.name:
                message_dict["name"] = msg.name

            openrouter_messages.append(message_dict)

        return openrouter_messages

    def _create_generation_result(
        self,
        completion: ChatCompletion,
        messages: List[ChatCompletionMessageParam],
    ) -> GenerationResult:
        """Create a GenerationResult from OpenRouter completion.

        Args:
            completion: OpenRouter chat completion
            messages: Original messages in OpenRouter format

        Returns:
            GenerationResult with completion details
        """
        content = completion.choices[0].message.content
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
            usage=completion.usage.model_dump() if completion.usage else None,
            metadata={
                "model": completion.model,
                "created": completion.created,
                "id": completion.id,
            },
        )

    async def generate(
        self, messages: Union[str, List[Message]], **kwargs: Any
    ) -> GenerationResult:
        """Generate text using OpenRouter's chat completion API.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options
                - temperature: Sampling temperature (0-2)
                - max_tokens: Maximum tokens to generate
                - stop: List of stop sequences
                - presence_penalty: Presence penalty (-2 to 2)
                - frequency_penalty: Frequency penalty (-2 to 2)

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """
        if not self._async_client:
            raise RuntimeError("OpenRouter client not initialized")

        try:
            openrouter_messages = self._convert_messages(messages)
            completion = await self._async_client.chat.completions.create(
                model=self.model,
                messages=openrouter_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs,
            )
            return self._create_generation_result(completion, openrouter_messages)

        except Exception as e:
            logger.error(f"OpenRouter generation failed: {e}")
            raise LLMError(f"OpenRouter generation failed: {e}")

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
        if not self._async_client:
            raise RuntimeError("OpenRouter client not initialized")

        try:
            openrouter_messages = self._convert_messages(messages)
            stream = await self._async_client.chat.completions.create(
                model=self.model,
                messages=openrouter_messages,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield GenerationChunk(
                        content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                        metadata={
                            "model": chunk.model,
                            "created": chunk.created,
                            "id": chunk.id,
                        },
                    )

        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            raise LLMError(f"OpenRouter streaming failed: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenRouter provider capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update(
            {
                "streaming": True,
                "chat_based": True,
                "supported_models": [
                    "openai/gpt-4",
                    "openai/gpt-3.5-turbo",
                    "anthropic/claude-2",
                    "google/palm-2",
                    "meta-llama/llama-2-70b-chat",
                ],
                "max_tokens": 4096,
            }
        )
        return capabilities
