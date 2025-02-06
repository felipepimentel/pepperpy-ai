"""OpenAI provider implementation for the Pepperpy framework.

This module provides integration with OpenAI's API, supporting both chat completion
and streaming capabilities.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, cast
from uuid import UUID, uuid4

from openai import AsyncOpenAI, AsyncStream
from openai.errors import OpenAIError  # type: ignore
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion import ChatCompletion
from pydantic import ConfigDict, Field, SecretStr

from pepperpy.core.types import Message, MessageType, Response, ResponseStatus
from pepperpy.monitoring import logger
from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderConfigError,
    ProviderError,
)


class OpenAIConfig(ProviderConfig):
    """OpenAI provider configuration.

    Attributes:
        api_key: OpenAI API key
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stop_sequences: Optional stop sequences
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
    """

    provider_type: str = Field(default="openai", description="The type of provider")
    api_key: SecretStr = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-4", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    stop_sequences: list[str] | None = Field(
        default=None, description="Optional stop sequences"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")

    model_config = ConfigDict(extra="forbid")


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration
        """
        # Convert to OpenAIConfig if needed
        openai_config = (
            config
            if isinstance(config, OpenAIConfig)
            else OpenAIConfig(**config.model_dump())
        )
        super().__init__(openai_config)
        self._client: AsyncOpenAI | None = None
        self._config = openai_config

    async def initialize(self) -> None:
        """Initialize the provider with configuration.

        Raises:
            ProviderError: If initialization fails due to invalid credentials
            ProviderConfigError: If configuration is invalid
            ProviderAPIError: If API connection fails
        """
        try:
            self._client = AsyncOpenAI(
                api_key=self._config.api_key.get_secret_value(),
                timeout=self._config.timeout,
                max_retries=self._config.max_retries,
            )
            logger.info("Initialized OpenAI provider", model=self._config.model)
        except OpenAIError as e:
            raise ProviderAPIError(f"Failed to initialize OpenAI provider: {e}") from e
        except ValueError as e:
            raise ProviderConfigError(f"Invalid OpenAI configuration: {e}") from e
        except Exception as e:
            raise ProviderError(
                f"Unexpected error initializing OpenAI provider: {e}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Cleaned up OpenAI provider")

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
            content = str(msg.content.get("text", ""))
            if msg.type == MessageType.QUERY:
                converted.append(
                    ChatCompletionUserMessageParam(role="user", content=content)
                )
            elif msg.type == MessageType.RESPONSE:
                converted.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=content
                    )
                )
            elif msg.type == MessageType.COMMAND:
                converted.append(
                    ChatCompletionSystemMessageParam(role="system", content=content)
                )
        return converted

    async def generate(self, messages: list[Message], **kwargs: Any) -> Response:
        """Generate a response from OpenAI.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the API

        Returns:
            Generated response

        Raises:
            ProviderError: If generation fails
        """
        try:
            if not self._client:
                raise ProviderError("Provider not initialized")

            response = await self._client.chat.completions.create(
                messages=self._convert_messages(messages),
                model=kwargs.get("model", self._config.model),
                temperature=kwargs.get("temperature", self._config.temperature),
                max_tokens=kwargs.get("max_tokens", self._config.max_tokens),
                stop=kwargs.get("stop_sequences"),
            )

            return Response(
                id=UUID(response.id),
                message_id=messages[-1].id,
                content={"text": response.choices[0].message.content},
                status=ResponseStatus.SUCCESS,
                metadata={
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else {},
                },
            )

        except Exception as e:
            return Response(
                id=uuid4(),
                message_id=messages[-1].id if messages else uuid4(),
                content={"error": str(e)},
                status=ResponseStatus.ERROR,
                metadata={"error": str(e)},
            )

    def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[Response]:
        """Stream responses from OpenAI.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the API

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            Exception: If streaming fails
        """

        async def stream_impl() -> AsyncIterator[Response]:
            try:
                if not self._client:
                    raise ProviderError("Provider not initialized")

                stream = await self._client.chat.completions.create(
                    messages=self._convert_messages(messages),
                    model=kwargs.get("model", self._config.model),
                    temperature=kwargs.get("temperature", self._config.temperature),
                    max_tokens=kwargs.get("max_tokens", self._config.max_tokens),
                    stop=kwargs.get("stop_sequences"),
                    stream=True,
                )

                async for chunk in stream:
                    if not hasattr(chunk, "choices"):
                        continue
                    choices = getattr(chunk, "choices", [])
                    if not choices:
                        continue
                    delta = getattr(choices[0], "delta", None)
                    if delta and hasattr(delta, "content") and delta.content:
                        yield Response(
                            id=UUID(chunk.id),
                            message_id=messages[-1].id,
                            content={"text": str(delta.content)},
                            status=ResponseStatus.SUCCESS,
                            metadata={
                                "model": chunk.model,
                                "index": choices[0].index,
                            },
                        )

            except Exception as e:
                yield Response(
                    id=uuid4(),
                    message_id=messages[-1].id if messages else uuid4(),
                    content={"error": str(e)},
                    status=ResponseStatus.ERROR,
                    metadata={"error": str(e)},
                )

        return stream_impl()

    async def _stream_response(
        self, response: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[str, None]:
        """Process streaming response.

        Args:
            response: Raw streaming response

        Returns:
            AsyncGenerator yielding text chunks
        """
        try:
            async for chunk in response:
                # Access chunk data safely
                if not hasattr(chunk, "choices"):
                    continue
                choices = getattr(chunk, "choices", [])
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                if delta and hasattr(delta, "content") and delta.content:
                    yield str(delta.content)
        except Exception as e:
            raise ProviderError(f"Failed to process stream: {e}") from e

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Generate completions for a prompt.

        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses
            **kwargs: Additional arguments

        Returns:
            Generated completion text or stream

        Raises:
            ProviderError: If completion fails
        """
        if not self._client:
            raise ProviderError("Provider not initialized")

        try:
            messages = [ChatCompletionUserMessageParam(role="user", content=prompt)]

            params = {
                "model": self._config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or self._config.max_tokens,
                "stop": kwargs.get(
                    "stop_sequences", getattr(self._config, "stop_sequences", None)
                ),
                "stream": stream,
            }

            response = await self._client.chat.completions.create(**params)

            if stream:
                if not isinstance(response, AsyncStream):
                    raise ProviderError("Expected streaming response")
                return self._stream_response(response)

            completion = cast(ChatCompletion, response)
            # Access completion data safely
            if not hasattr(completion, "choices"):
                raise ProviderError("No choices in completion response")

            choices = getattr(completion, "choices", [])
            if not choices:
                raise ProviderError("Empty choices in completion response")

            message = choices[0].message
            if not message or not hasattr(message, "content"):
                raise ProviderError("Invalid completion message format")

            return str(message.content)

        except Exception as e:
            raise ProviderError(f"Failed to complete prompt: {e}") from e

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate chat completions.

        Args:
            messages: List of chat messages
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            stop_sequences: Optional stop sequences override
            stream: Whether to stream responses

        Returns:
            Generated completion text or stream

        Raises:
            ProviderError: If chat completion fails
        """
        if not self._client or not self._config:
            raise ProviderError("Provider not initialized")

        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            response = await self._client.chat.completions.create(
                model=model or self._config.model,
                messages=openai_messages,
                temperature=temperature or self._config.temperature,
                max_tokens=max_tokens or self._config.max_tokens,
                stop=stop_sequences or self._config.stop_sequences,
                stream=stream,
            )

            if stream:
                if not isinstance(response, AsyncStream):
                    raise ProviderError("Expected streaming response")
                return self._stream_response(response)

            # Cast to ChatCompletion for non-streaming response
            completion = cast(ChatCompletion, response)
            if not hasattr(completion, "choices") or not completion.choices:
                raise ProviderError("No completion choices returned")

            message = completion.choices[0].message
            if not message or not hasattr(message, "content"):
                raise ProviderError("Invalid completion message format")

            return str(message.content)

        except Exception as e:
            raise ProviderError(f"OpenAI chat completion failed: {e}") from e

    async def embed(
        self,
        text: str,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Additional arguments

        Returns:
            List of embedding values

        Raises:
            ProviderError: If embedding fails
        """
        if not self._client or not self._config:
            raise ProviderError("Provider not initialized")

        try:
            response = await self._client.embeddings.create(
                model=kwargs.get("model", "text-embedding-ada-002"),
                input=text,
            )
            return response.data[0].embedding

        except Exception as e:
            raise ProviderError(f"OpenAI embedding failed: {e}") from e
