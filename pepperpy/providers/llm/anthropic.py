"""Anthropic language model provider.

This module provides the Anthropic implementation of the LLM provider interface.
It handles:
- Anthropic API integration
- Model configuration
- Token counting
- Error handling
"""

import os
from typing import Any, List, Optional
from uuid import uuid4

from anthropic import AsyncAnthropic
from anthropic.types import (
    CompletionCreateParams,
    Message,
    MessageParam,
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

# Valid Anthropic models
VALID_MODELS = frozenset({
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-2.1",
    "claude-2.0",
})

# Role mapping
ROLE_MAP = {
    "system": "system",
    "user": "user",
    "assistant": "assistant",
}


class AnthropicProvider(BaseLLMProvider):
    """Anthropic language model provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        self._client: Optional[AsyncAnthropic] = None

    async def initialize(self) -> None:
        """Initialize the provider.

        This method sets up the Anthropic client.

        Raises:
            ConfigurationError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Get API key from environment
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ConfigurationError(
                    "ANTHROPIC_API_KEY environment variable not set"
                )

            # Initialize client
            self._client = AsyncAnthropic(api_key=api_key)
            self._initialized = True

            logger.info("Anthropic provider initialized", extra={"model": self.model})

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Anthropic provider: {e}")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.close()
        self._initialized = False
        logger.info("Anthropic provider cleaned up")

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
        if not (0 <= self.temperature <= 1):
            raise ConfigurationError("Temperature must be between 0 and 1")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ConfigurationError("max_tokens must be positive")

    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using the Anthropic API.

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
            raise ProviderError("Anthropic client not available")

        try:
            # Convert messages to Anthropic format
            anthropic_messages: List[MessageParam] = []
            system_message = None

            for msg in messages:
                if not msg.content:
                    continue  # Skip empty messages

                role = ROLE_MAP.get(msg.role)
                if not role:
                    raise ProviderError(f"Invalid message role: {msg.role}")

                if role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append(Message(role=role, content=msg.content))

            if not anthropic_messages:
                raise ProviderError("No valid messages provided")

            # Create message parameters
            params = CompletionCreateParams(
                model=self.model,
                messages=anthropic_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                system=system_message,
                **kwargs,
            )

            # Call API
            completion = await self._client.messages.create(**params)

            # Extract response
            content = completion.content[0].text
            if not content:
                raise ProviderError("Empty response from Anthropic API")

            # Create response object
            return LLMResponse(
                id=uuid4(),
                content=content,
                model=completion.model,
                usage={
                    "input_tokens": completion.usage.input_tokens,
                    "output_tokens": completion.usage.output_tokens,
                    "total_tokens": (
                        completion.usage.input_tokens + completion.usage.output_tokens
                    ),
                },
                finish_reason=completion.stop_reason,
            )

        except Exception as e:
            raise ProviderError(
                f"Failed to generate response: {e}",
                provider_type="anthropic",
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
            # Use anthropic's token counting
            if not self._client:
                raise ProviderError("Anthropic client not available")
            count = await self._client.count_tokens(text)
            return count
        except Exception as e:
            raise ProviderError(
                f"Failed to count tokens: {e}",
                provider_type="anthropic",
                details={"error": str(e)},
            )
