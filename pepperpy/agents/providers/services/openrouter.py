"""OpenRouter provider implementation for the Pepperpy framework.

This module provides integration with OpenRouter's API, supporting both chat completion
and streaming capabilities.
"""

import os
from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from typing import Any, List, TypeAlias, TypeVar, cast
from uuid import uuid4

from openai import APIError, AsyncOpenAI, AsyncStream, OpenAIError
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import ConfigDict, Field, SecretStr, field_validator

from pepperpy.core.messages import Message
from pepperpy.core.types import MessageContent, MessageType, Response, ResponseStatus
from pepperpy.monitoring import logger
from pepperpy.providers.base import (
    BaseProvider,
    ProviderConfig,
    StreamKwargs,
)
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderConfigError,
    ProviderError,
    ProviderInitError,
)

# Configure logger
logger = logger.bind()

# Type variable for OpenRouter response types
ResponseT = TypeVar("ResponseT", ChatCompletion, ChatCompletionChunk)

# Type aliases for OpenRouter parameters
OpenRouterMessages = Sequence[ChatCompletionMessageParam]
OpenRouterStop = list[str] | NotGiven
ModelParam: TypeAlias = str
TemperatureParam: TypeAlias = float
MaxTokensParam: TypeAlias = int


class OpenRouterConfig(ProviderConfig):
    """OpenRouter provider configuration.

    Attributes
    ----------
        api_key: OpenRouter API key
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stop_sequences: Optional stop sequences
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    """

    provider_type: str = Field(default="openrouter", description="The type of provider")
    api_key: SecretStr = Field(default=SecretStr(""), description="OpenRouter API key")
    model: str = Field(default="openai/gpt-4", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    stop_sequences: list[str] | None = Field(
        default=None, description="Optional stop sequences"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")

    model_config = ConfigDict(extra="forbid")

    @field_validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v

    @field_validator("max_tokens")
    def validate_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_tokens must be greater than 0")
        return v

    @field_validator("timeout")
    def validate_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("timeout must be greater than 0")
        return v

    @field_validator("max_retries")
    def validate_max_retries(cls, v: int) -> int:
        if v < 0:
            raise ValueError("max_retries must be greater than or equal to 0")
        return v


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider.

        Args:
        ----
            config: Provider configuration

        """
        # Get API key from config or environment variable
        api_key = (
            config.api_key
            if config.api_key
            else SecretStr(os.getenv("PEPPERPY_API_KEY", ""))
        )

        # Convert to OpenRouterConfig if needed
        openrouter_config = (
            config
            if isinstance(config, OpenRouterConfig)
            else OpenRouterConfig(**{
                **config.model_dump(),
                "api_key": api_key,
            })
        )
        super().__init__(openrouter_config)
        self._client: AsyncOpenAI | None = None
        self._config = openrouter_config

    async def initialize(self) -> None:
        """Initialize the provider with configuration.

        Raises
        ------
            ProviderError: If initialization fails due to invalid credentials
            ProviderConfigError: If configuration is invalid
            ProviderAPIError: If API connection fails

        """
        try:
            # Initialize the base provider first
            await super().initialize()

            self._client = AsyncOpenAI(
                api_key=self._config.api_key.get_secret_value(),
                timeout=self._config.timeout,
                max_retries=self._config.max_retries,
                base_url="https://openrouter.ai/api/v1",
            )
            logger.info(
                f"Initialized OpenRouter provider - Model: {self._config.model}"
            )
        except OpenAIError as api_error:  # type: ignore
            msg = str(api_error)  # type: ignore
            raise ProviderAPIError(msg) from api_error
        except ValueError as val_error:
            msg = str(val_error)
            raise ProviderConfigError(msg) from val_error
        except Exception as exc:
            msg = str(exc)
            raise ProviderInitError(
                message=msg, provider_type="openrouter", details={"error": str(exc)}
            ) from exc

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            try:
                await self._client.close()
                self._client = None
                await super().cleanup()
                logger.info("Cleaned up OpenRouter provider")
            except Exception as exc:  # type: ignore
                logger.error(f"Error during cleanup: {exc!r}")
                raise ProviderError(
                    message=f"Cleanup failed: {exc}",
                    provider_type="openrouter",
                    details={"error": str(exc)},
                ) from exc

    def _convert_messages(
        self, messages: list[Message]
    ) -> list[ChatCompletionMessageParam]:
        """Convert messages to OpenAI format.

        Args:
        ----
            messages: List of messages to convert

        Returns:
        -------
            List of messages in OpenAI format

        """
        converted: list[ChatCompletionMessageParam] = []
        for msg in messages:
            content = str(msg.content)
            role = msg.metadata.get("role", "user") if msg.metadata else "user"

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

    async def generate(self, messages: list[Message], **kwargs: Any) -> Response:
        """Generate a response using OpenRouter's API.

        Args:
        ----
            messages: List of messages to generate from
            **kwargs: Additional generation parameters

        Returns:
        -------
            The generated response

        Raises:
        ------
            ProviderError: If generation fails

        """
        self._check_initialized()

        try:
            if not self._client:
                raise ProviderError("OpenRouter client not initialized")

            # Convert messages to OpenRouter format
            openai_messages = self._convert_messages(messages)

            # Get generation parameters
            model = str(kwargs.get("model", self._config.model))
            temperature = float(kwargs.get("temperature", self._config.temperature))
            max_tokens = int(kwargs.get("max_tokens", self._config.max_tokens))

            # Generate response
            response = await self._client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response content
            content = response.choices[0].message.content if response.choices else ""
            message_content: MessageContent = {
                "type": MessageType.RESPONSE,
                "content": {"text": content},
            }
            return Response(
                id=uuid4(),
                message_id=str(messages[-1].id),
                content=message_content,
                status=ResponseStatus.SUCCESS,
            )

        except (OpenAIError, APIError, ValueError, Exception) as e:
            logger.error("OpenRouter generation failed", error=str(e))
            raise ProviderError(
                message=str(e),
                provider_type="openrouter",
                details={"error": str(e)},
            ) from e

    async def stream(
        self, messages: list[Message], **kwargs: StreamKwargs
    ) -> AsyncIterator[Response]:
        """Stream responses from OpenRouter's API.

        Args:
        ----
            messages: List of messages to generate from
            **kwargs: Additional generation parameters

        Returns:
        -------
            An async iterator of response chunks

        Raises:
        ------
            ProviderError: If streaming fails

        """
        self._check_initialized()

        try:
            if not self._client:
                raise ProviderError("OpenRouter client not initialized")

            # Convert messages to OpenRouter format
            openai_messages = self._convert_messages(messages)

            # Get generation parameters
            model = str(kwargs.get("model", self._config.model))
            temperature = self._config.temperature
            max_tokens = self._config.max_tokens

            # Override with kwargs if provided
            if "temperature" in kwargs:
                temp_val = cast(dict[str, Any], kwargs)["temperature"]
                if temp_val is not None:
                    temperature = float(temp_val)
            if "max_tokens" in kwargs:
                tokens_val = cast(dict[str, Any], kwargs)["max_tokens"]
                if tokens_val is not None:
                    max_tokens = int(tokens_val)

            # Create streaming response
            stream = await self._client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Stream response chunks
            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if not delta.content:
                    continue

                yield Response(
                    id=uuid4(),
                    message_id=str(messages[-1].id),
                    content={
                        "type": MessageType.RESPONSE,
                        "content": {"text": delta.content},
                    },
                    status=ResponseStatus.SUCCESS,
                )

        except Exception as e:
            self._logger.error(
                "OpenRouter streaming failed",
                error=str(e),
                model=self._config.model,
            )
            raise ProviderAPIError(str(e)) from e

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the provider's model.

        Args:
        ----
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
        -------
            Generated text or async generator of text chunks if streaming

        Raises:
        ------
            ProviderError: If the API call fails or rate limit is exceeded
            RuntimeError: If provider is not initialized

        """
        if not self._client:
            raise ProviderInitError(
                message="Provider not initialized", provider_type="openrouter"
            )

        try:
            messages = [ChatCompletionUserMessageParam(role="user", content=prompt)]
            model_params = kwargs.get("model_params", {})
            stop_sequences = kwargs.get("stop_sequences")

            model = model_params.get("model", self._config.model)
            max_tokens_value = max_tokens or self._config.max_tokens
            stop = (
                cast(list[str], stop_sequences)
                if stop_sequences is not None
                else NOT_GIVEN
            )

            if stream:
                stream_response = await self._client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens_value,
                    stream=True,
                    stop=stop,
                )
                return self._stream_response(stream_response)
            else:
                completion = await self._client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens_value,
                    stream=False,
                    stop=stop,
                )
                return completion.choices[0].message.content or ""

        except OpenAIError as api_error:  # type: ignore[misc,attr-defined]
            error_msg: str = "OpenRouter API error"
            if hasattr(api_error, "message"):  # type: ignore[attr-defined]
                error_msg = f"{error_msg}: {api_error.message}"  # type: ignore[attr-defined]
            elif hasattr(api_error, "code"):  # type: ignore[attr-defined]
                error_msg = f"{error_msg} (code: {api_error.code})"  # type: ignore[attr-defined]
            else:
                error_msg = f"{error_msg}: {api_error!s}"
            raise ProviderError(error_msg) from api_error
        except Exception as exc:
            msg = str(exc)
            raise ProviderError(f"Unexpected error: {msg}") from exc

    async def _stream_response(
        self, response: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[str, None]:
        """Process streaming response.

        Args:
        ----
            response: Raw streaming response

        Returns:
        -------
            AsyncGenerator[str, None]: Stream of text chunks

        """
        async for chunk in response:
            chunk_choices: list[ChunkChoice] = chunk.choices
            if not chunk_choices:
                continue
            delta = chunk_choices[0].delta
            if delta.content:
                yield delta.content

    async def chat_completion(
        self,
        model: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> str:
        """Run a chat completion with the given parameters.

        Args:
        ----
            model: The model to use
            messages: The messages to send to the model
            **kwargs: Additional parameters for the model

        Returns:
        -------
            The model's response

        Raises:
        ------
            ProviderError: If the chat completion fails
            ValueError: If messages list is empty

        """
        if not self._client:
            raise ProviderInitError(
                message="Provider not initialized", provider_type="openrouter"
            )

        if not messages:
            raise ValueError("Messages list cannot be empty")

        try:
            temperature = float(kwargs.get("temperature", self._config.temperature))
            max_tokens = int(kwargs.get("max_tokens", self._config.max_tokens))
            stop_sequences = kwargs.get("stop_sequences")
            stop = (
                cast(list[str], stop_sequences)
                if stop_sequences is not None
                else NOT_GIVEN
            )

            converted_messages = self._convert_messages(messages)
            response = await self._client.chat.completions.create(
                messages=converted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                stop=stop,
            )

            return response.choices[0].message.content or ""

        except OpenAIError as api_error:  # type: ignore[misc,attr-defined]
            error_msg: str = "OpenRouter API error"
            if hasattr(api_error, "message"):  # type: ignore[attr-defined]
                error_msg = f"{error_msg}: {api_error.message}"  # type: ignore[attr-defined]
            elif hasattr(api_error, "code"):  # type: ignore[attr-defined]
                error_msg = f"{error_msg} (code: {api_error.code})"  # type: ignore[attr-defined]
            else:
                error_msg = f"{error_msg}: {api_error!s}"
            raise ProviderError(error_msg) from api_error
        except Exception as exc:
            msg = str(exc)
            raise ProviderError(f"Unexpected error: {msg}") from exc

    async def send_message(self, message: str) -> Response:
        """Send a message and get a response.

        Args:
        ----
            message: Message to send.

        Returns:
        -------
            Response: Provider response.

        Raises:
        ------
            ProviderError: If sending message fails

        """
        self._check_initialized()

        try:
            if not self._client:
                raise ProviderError("OpenRouter client not initialized")

            # Convert message to OpenRouter format
            openai_messages = [
                ChatCompletionUserMessageParam(role="user", content=message)
            ]

            # Generate response
            response = await self._client.chat.completions.create(
                model=self._config.model,
                messages=openai_messages,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
                stop=self._config.stop_sequences or NOT_GIVEN,
            )

            # Extract response content
            content = response.choices[0].message.content or ""

            # Create response object
            return Response(
                id=uuid4(),
                message_id=str(uuid4()),
                content={"type": MessageType.RESPONSE, "content": {"text": content}},
                status=ResponseStatus.SUCCESS,
            )

        except (OpenAIError, APIError, ValueError, Exception) as error:
            raise ProviderError(
                message=f"Failed to send message: {error}",
                provider_type="openrouter",
                details={"error": str(error)},
            ) from error
