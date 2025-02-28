"""OpenAI provider implementation.

This module provides integration with OpenAI's API, supporting both chat completion
and streaming capabilities.
"""

from collections.abc import AsyncGenerator
from typing import Any, Optional, Union

from openai import APIError, AsyncOpenAI, AsyncStream, OpenAIError
from openai.types.chat import (
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from pydantic import Field, SecretStr

from pepperpy.core.errors import ConfigurationError
from pepperpy.common.messages import Message, ProviderMessage, ProviderResponse
from pepperpy.common.monitoring import logger
from pepperpy.llm.base import LLMConfig, LLMProvider


class OpenAIConfig(LLMConfig):
    """OpenAI provider configuration.

    Attributes:
        api_key: OpenAI API key
        model: Model to use (default: gpt-4)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (default: 2048)
        stop_sequences: Optional stop sequences
        timeout: Request timeout in seconds (default: 30.0)
        max_retries: Maximum number of retries (default: 3)
    """

    api_key: SecretStr = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-4", description="Model to use")


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def __init__(self, config: OpenAIConfig) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client: Optional[AsyncOpenAI] = None
        self._config = config

    async def _initialize_service(self) -> None:
        """Initialize the OpenAI client.

        Raises:
            ProviderError: If initialization fails
        """
        try:
            self._client = AsyncOpenAI(
                api_key=self._config.api_key.get_secret_value(),
                timeout=self._config.timeout,
                max_retries=self._config.max_retries,
            )
            logger.info(f"Initialized OpenAI provider - Model: {self._config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    async def _cleanup_service(self) -> None:
        """Clean up the OpenAI client."""
        if self._client:
            try:
                await self._client.close()
                self._client = None
                logger.info("Cleaned up OpenAI client")
            except Exception as e:
                logger.error(f"Error during OpenAI cleanup: {e}")
                raise

    def _convert_messages(
        self, messages: list[Message]
    ) -> list[ChatCompletionMessageParam]:
        """Convert internal message format to OpenAI format.

        Args:
            messages: List of messages to convert

        Returns:
            List of OpenAI chat completion messages
        """
        converted: list[ChatCompletionMessageParam] = []
        for msg in messages:
            content = str(msg.content)
            role = msg.metadata.get("role", "user")

            if role == "user":
                converted.append(
                    ChatCompletionUserMessageParam(role="user", content=content)
                )
            elif role == "assistant":
                converted.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=content
                    )
                )
            elif role == "system":
                converted.append(
                    ChatCompletionSystemMessageParam(role="system", content=content)
                )

        return converted

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message.

        Args:
            message: Provider message to process

        Returns:
            Provider response or async generator of responses

        Raises:
            ProviderError: If message processing fails
            ConfigurationError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ConfigurationError("Provider not initialized")

        try:
            if not self._client:
                raise ConfigurationError("OpenAI client not initialized")

            # Convert message to OpenAI format
            messages = self._convert_messages([message])

            # Get generation parameters
            temperature = message.metadata.get("temperature", self._config.temperature)
            max_tokens = message.metadata.get("max_tokens", self._config.max_tokens)
            stream = message.metadata.get("stream", False)

            # Generate response
            if stream:
                response = await self._client.chat.completions.create(
                    model=self._config.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                return self._stream_response(response)
            else:
                response = await self._client.chat.completions.create(
                    model=self._config.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                return ProviderResponse(
                    content=response.choices[0].message.content or "",
                    metadata={
                        "model": response.model,
                        "usage": response.usage.model_dump() if response.usage else {},
                    },
                )

        except (OpenAIError, APIError) as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise

    async def _stream_response(
        self, response: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[ProviderResponse, None]:
        """Process streaming response from OpenAI.

        Args:
            response: OpenAI streaming response

        Yields:
            Provider responses
        """
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield ProviderResponse(
                    content=chunk.choices[0].delta.content,
                    metadata={"model": chunk.model},
                )

    async def embed(
        self,
        text: str,
        *,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings for the given text.

        Args:
            text: Text to generate embeddings for
            model: Optional model to use (default: text-embedding-3-small)
            dimensions: Optional number of dimensions
            **kwargs: Additional model-specific parameters

        Returns:
            List of embedding values

        Raises:
            ProviderError: If embedding generation fails
        """
        if not self.is_initialized:
            raise ConfigurationError("Provider not initialized")

        try:
            if not self._client:
                raise ConfigurationError("OpenAI client not initialized")

            response = await self._client.embeddings.create(
                model=model or "text-embedding-3-small",
                input=text,
                dimensions=dimensions,
                **kwargs,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
