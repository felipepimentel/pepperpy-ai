"""OpenAI language model provider.

This module provides the OpenAI implementation of the LLM provider interface.
It handles:
- OpenAI API integration
- Model configuration
- Token counting
- Error handling
"""

import os
from typing import Any, List, Optional
from uuid import uuid4

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.providers.base import ProviderError
from pepperpy.providers.llm.base import (
    BaseLLMProvider,
    LLMConfig,
    LLMMessage,
    LLMResponse,
)

# Configure logging
logger = get_logger(__name__)

# Valid OpenAI models
VALID_MODELS = frozenset({
    "gpt-4",
    "gpt-4-turbo-preview",
    "gpt-3.5-turbo",
})


def create_message_param(msg: LLMMessage) -> ChatCompletionMessageParam:
    """Create a ChatCompletionMessageParam from an LLMMessage.

    Args:
        msg: The message to convert

    Returns:
        OpenAI API message parameter

    Raises:
        ProviderError: If message role is invalid
    """
    if not msg.content:
        raise ProviderError("Message content cannot be empty")

    base_params = {"content": msg.content}

    try:
        if msg.role == "system":
            return ChatCompletionSystemMessageParam(role="system", **base_params)
        elif msg.role == "user":
            return ChatCompletionUserMessageParam(role="user", **base_params)
        elif msg.role == "assistant":
            return ChatCompletionAssistantMessageParam(role="assistant", **base_params)
        elif msg.role == "tool":
            if not msg.name:
                raise ProviderError("Tool messages must have a name")
            return ChatCompletionToolMessageParam(
                role="tool", tool_call_id=msg.name, **base_params
            )
        else:
            raise ProviderError(f"Invalid message role: {msg.role}")
    except TypeError as e:
        raise ProviderError(f"Failed to create message parameter: {e}")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI language model provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize the provider.

        This method sets up the OpenAI client.

        Raises:
            ConfigurationError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Get API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ConfigurationError("OPENAI_API_KEY environment variable not set")

            # Initialize client
            self._client = AsyncOpenAI(api_key=api_key)
            self._initialized = True

            logger.info("OpenAI provider initialized", extra={"model": self.model})

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize OpenAI provider: {e}")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.close()
        self._initialized = False
        logger.info("OpenAI provider cleaned up")

    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        if not self.model:
            raise ConfigurationError("Model must be specified")
        if self.model not in VALID_MODELS:
            raise ConfigurationError(
                f"Invalid model: {self.model}. Must be one of: {VALID_MODELS}"
            )
        if not (0 <= self.temperature <= 2):
            raise ConfigurationError("Temperature must be between 0 and 2")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ConfigurationError("max_tokens must be positive")
        if not (-2.0 <= self.presence_penalty <= 2.0):
            raise ConfigurationError("presence_penalty must be between -2.0 and 2.0")
        if not (-2.0 <= self.frequency_penalty <= 2.0):
            raise ConfigurationError("frequency_penalty must be between -2.0 and 2.0")

    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using the OpenAI API.

        Args:
            messages: List of messages for context
            **kwargs: Additional parameters to pass to the API

        Returns:
            Model response

        Raises:
            ProviderError: If generation fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")
        if not self._client:
            raise ProviderError("OpenAI client not available")

        try:
            # Convert messages to OpenAI format
            openai_messages = [
                create_message_param(msg) for msg in messages if msg.content
            ]

            if not openai_messages:
                raise ProviderError("No valid messages provided")

            # Call API
            completion: ChatCompletion = await self._client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=self.stop,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                **kwargs,
            )

            # Extract response
            choice = completion.choices[0]
            content = choice.message.content
            if not content:
                raise ProviderError("Empty response from OpenAI API")

            # Create response object
            usage = completion.usage
            if not usage:
                raise ProviderError("Missing usage information from OpenAI API")

            return LLMResponse(
                id=uuid4(),
                content=content,
                model=completion.model,
                usage={
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                finish_reason=choice.finish_reason,
            )

        except Exception as e:
            raise ProviderError(
                f"Failed to generate response: {e}",
                provider_type="openai",
                details={"error": str(e)},
            )

    async def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Raises:
            ProviderError: If token counting fails
        """
        try:
            # Use tiktoken for token counting
            # Note: tiktoken is a required dependency, added to pyproject.toml
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            raise ProviderError(
                "tiktoken package not installed. Please install it with: pip install tiktoken"
            )
        except Exception as e:
            raise ProviderError(
                f"Failed to count tokens: {e}",
                provider_type="openai",
                details={"error": str(e)},
            )
