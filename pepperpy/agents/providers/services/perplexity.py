"""Perplexity provider implementation for the Pepperpy framework.

This module provides integration with Perplexity's API, supporting both chat completion
and streaming capabilities.
"""

from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from typing import Any, Literal, Mapping, TypeAlias, TypeVar, cast
from uuid import UUID, uuid4

from openai import APIError, AsyncOpenAI, AsyncStream, OpenAIError
from openai._types import NotGiven, Omit
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
from pydantic import ConfigDict, Field, SecretStr

from pepperpy.core.types import Message, MessageType, Response, ResponseStatus
from pepperpy.monitoring import logger
from pepperpy.providers.base import (
    BaseProvider,
    GenerateKwargs,
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

# Type variable for Perplexity response types
ResponseT = TypeVar("ResponseT", ChatCompletion, ChatCompletionChunk)

# Type alias for Perplexity errors
PerplexityErrorType = OpenAIError | APIError | ValueError | Exception  # type: ignore

# Type aliases for Perplexity parameters
PerplexityMessages = Sequence[ChatCompletionMessageParam]
PerplexityStop = list[str] | NotGiven
ModelParam: TypeAlias = str
TemperatureParam: TypeAlias = float
MaxTokensParam: TypeAlias = int


class PerplexityConfig(ProviderConfig):
    """Perplexity provider configuration.

    Attributes:
        api_key: Perplexity API key
        model: Model to use (e.g. llama-3.1-sonar-small-128k-online)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stop_sequences: Optional stop sequences
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
    """

    provider_type: str = Field(default="perplexity", description="The type of provider")
    api_key: SecretStr = Field(..., description="Perplexity API key")
    model: str = Field(
        default="llama-3.1-sonar-small-128k-online", description="Model to use"
    )
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    stop_sequences: list[str] | None = Field(
        default=None, description="Optional stop sequences"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")

    model_config = ConfigDict(extra="forbid")


class PerplexityProvider(BaseProvider):
    """Perplexity provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider.

        Args:
            config: Provider configuration
        """
        # Convert to PerplexityConfig if needed
        perplexity_config = (
            config
            if isinstance(config, PerplexityConfig)
            else PerplexityConfig(**config.model_dump())
        )
        super().__init__(perplexity_config)
        self._client: AsyncOpenAI | None = None
        self._config = perplexity_config

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
                base_url="https://api.perplexity.ai",
            )
            logger.info(
                f"Initialized Perplexity provider - Model: {self._config.model}"
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
                message=msg, provider_type="perplexity", details={"error": str(exc)}
            ) from exc

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            try:
                await self._client.close()
                self._client = None
                logger.info("Cleaned up Perplexity provider")
            except Exception as exc:  # type: ignore
                logger.error(f"Error during cleanup: {exc!r}")
                raise ProviderError(
                    message=f"Cleanup failed: {exc}",
                    provider_type="perplexity",
                    details={"error": str(exc)},
                ) from exc

    def _convert_messages(
        self, messages: list[Message]
    ) -> list[ChatCompletionMessageParam]:
        """Convert internal message format to Perplexity format.

        Args:
            messages: List of messages to convert

        Returns:
            List of Perplexity chat completion messages
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

    async def generate(
        self, messages: list[Message], **kwargs: GenerateKwargs
    ) -> Response:
        """Generate a response from Perplexity.

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
                raise ProviderInitError(
                    message="Provider not initialized", provider_type="perplexity"
                )

            model_params = kwargs.get("model_params", {})
            stop_sequences = kwargs.get("stop_sequences")

            converted_messages = self._convert_messages(messages)
            model = str(model_params.get("model", self._config.model))
            temperature = float(
                model_params.get("temperature", self._config.temperature)
            )
            max_tokens = int(model_params.get("max_tokens", self._config.max_tokens))
            stop = (
                cast(list[str], stop_sequences)
                if stop_sequences is not None
                else NotGiven()
            )

            response = await self._client.chat.completions.create(
                messages=converted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                stop=stop,
            )

            # Try to parse response ID as UUID, fallback to new UUID if invalid
            try:
                response_id = UUID(response.id)
            except ValueError:
                response_id = uuid4()
                logger.debug(
                    "Invalid UUID from provider, generated new one",
                    original_id=response.id,
                    new_id=str(response_id),
                )

            # Convert usage data to strings
            usage_data = {}
            if response.usage:
                usage_data = {
                    k: str(v) if v is not None else ""
                    for k, v in response.usage.model_dump().items()
                }

            return Response(
                id=response_id,
                message_id=messages[-1].id,
                content={"text": response.choices[0].message.content},
                status=ResponseStatus.SUCCESS,
                metadata={
                    "model": response.model,
                    "usage": usage_data,
                    "original_id": response.id,  # Store original ID in metadata
                },
            )

        except Exception as error:
            return Response(
                id=uuid4(),
                message_id=messages[-1].id if messages else uuid4(),
                content={"error": str(error)},
                status=ResponseStatus.ERROR,
                metadata={"error": str(error)},
            )

    async def stream(
        self, messages: list[Message], **kwargs: StreamKwargs
    ) -> AsyncIterator[Response]:
        """Stream responses from Perplexity.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the API

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            Exception: If streaming fails
        """
        try:
            if not self._client:
                raise ProviderInitError(
                    message="Provider not initialized", provider_type="perplexity"
                )

            model_params = kwargs.get("model_params", {})
            stop_sequences = kwargs.get("stop_sequences")

            converted_messages = self._convert_messages(messages)
            model = str(model_params.get("model", self._config.model))
            temperature = float(
                model_params.get("temperature", self._config.temperature)
            )
            max_tokens = int(model_params.get("max_tokens", self._config.max_tokens))
            stop = (
                cast(list[str], stop_sequences)
                if stop_sequences is not None
                else NotGiven()
            )

            stream = await self._client.chat.completions.create(
                messages=converted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                stop=stop,
            )

            async for chunk in stream:
                chunk_choices: Sequence[ChunkChoice] = chunk.choices
                if not chunk_choices:
                    continue
                choice = chunk_choices[0]
                if choice.delta and choice.delta.content:
                    # Try to parse chunk ID as UUID, fallback to new UUID if invalid
                    try:
                        chunk_id = UUID(chunk.id)
                    except ValueError:
                        chunk_id = uuid4()
                        logger.debug(
                            "Invalid UUID from provider in stream, generated new one",
                            original_id=chunk.id,
                            new_id=str(chunk_id),
                        )

                    # Convert usage data to strings if present
                    usage_data = {}
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage_data = {
                            k: str(v) if v is not None else ""
                            for k, v in chunk.usage.model_dump().items()
                        }

                    yield Response(
                        id=chunk_id,
                        message_id=messages[-1].id,
                        content={"text": str(choice.delta.content)},
                        status=ResponseStatus.SUCCESS,
                        metadata={
                            "model": chunk.model,
                            "index": choice.index,
                            "usage": usage_data,
                            "original_id": chunk.id,  # Store original ID in metadata
                        },
                    )

        except Exception as error:
            yield Response(
                id=uuid4(),
                message_id=messages[-1].id if messages else uuid4(),
                content={"error": str(error)},
                status=ResponseStatus.ERROR,
                metadata={"error": str(error)},
            )

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
            prompt: The prompt to complete
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text or async generator of text chunks if streaming

        Raises:
            ProviderError: If the API call fails or rate limit is exceeded
            RuntimeError: If provider is not initialized
        """
        if not self._client:
            raise ProviderInitError(
                message="Provider not initialized", provider_type="perplexity"
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
                else NotGiven()
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
            error_msg: str = "Perplexity API error"
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
            response: Raw streaming response

        Returns:
            AsyncGenerator[str, None]: Stream of text chunks
        """
        async for chunk in response:
            chunk_choices: list[ChunkChoice] = chunk.choices
            if not chunk_choices:
                continue
            delta = chunk_choices[0].delta
            if delta.content:
                yield delta.content
