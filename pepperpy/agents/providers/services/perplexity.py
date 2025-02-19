"""Perplexity provider implementation for the Pepperpy framework.

This module provides integration with Perplexity's API, supporting both chat completion
and streaming capabilities.
"""

from collections.abc import AsyncGenerator, Sequence
from typing import Any, Dict, Literal, TypeAlias, TypeVar, Union

from openai import APIError, AsyncOpenAI, AsyncStream, OpenAIError
from openai._types import NotGiven
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
from pydantic import ConfigDict, Field, SecretStr

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.messages import Message, ProviderMessage, ProviderResponse
from pepperpy.core.providers.base import BaseProvider, ProviderConfig
from pepperpy.core.providers.errors import (
    ProviderConfigurationError as ProviderConfigError,
)
from pepperpy.core.providers.errors import (
    ProviderError,
)
from pepperpy.core.providers.errors import (
    ProviderResourceError as ProviderInitError,
)
from pepperpy.core.providers.errors import (
    ProviderRuntimeError as ProviderAPIError,
)

# Configure logger
logger = get_logger(__name__)

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

# Type aliases for provider parameters
GenerateKwargs = Dict[str, Any]
StreamKwargs = Dict[str, Any]


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

    api_key: SecretStr = Field(default=SecretStr(""), description="Perplexity API key")
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
            else PerplexityConfig(
                type="perplexity",
                config={
                    **config.config,
                    "api_key": config.config.get("api_key", ""),
                },
            )
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
            self._initialized = True
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
                await super().cleanup()
                self._initialized = False
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
                raise ProviderError("Perplexity client not initialized")

            # Convert message to Perplexity format
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

        except OpenAIError as api_error:  # type: ignore
            msg = str(api_error)  # type: ignore
            raise ProviderAPIError(msg) from api_error
        except Exception as exc:
            msg = str(exc)
            raise ProviderError(
                message=msg,
                provider_type="perplexity",
                details={"error": str(exc)},
            ) from exc

    async def _stream_response(
        self, response: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[ProviderResponse, None]:
        """Stream response chunks.

        Args:
            response: Perplexity response stream

        Yields:
            Provider response chunks
        """
        async for chunk in response:
            if chunk.choices:
                choice = chunk.choices[0]
                if choice.delta.content:
                    yield ProviderResponse(
                        content=choice.delta.content,
                        metadata={
                            "model": chunk.model,
                            "finish_reason": choice.finish_reason,
                        },
                    )

    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        dimensions: int | None = None,
        encoding_format: Literal["float", "base64"] | None = None,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings for the given text.

        Args:
            text: Text to generate embeddings for
            model: Model to use for embeddings
            dimensions: Number of dimensions for embeddings
            encoding_format: Encoding format for embeddings
            **kwargs: Additional keyword arguments

        Returns:
            List of embeddings

        Raises:
            ProviderError: If embedding generation fails
            ConfigurationError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ConfigurationError("Provider not initialized")

        try:
            if not self._client:
                raise ProviderError("Perplexity client not initialized")

            # Get embedding parameters
            model_name = model or "text-embedding-3-small"
            dimensions_value = dimensions or 1536
            encoding = encoding_format or "float"

            # Generate embeddings
            response = await self._client.embeddings.create(
                input=text,
                model=model_name,
                dimensions=dimensions_value,
                encoding_format=encoding,
                **kwargs,
            )

            # Return embeddings
            return response.data[0].embedding

        except OpenAIError as api_error:  # type: ignore
            msg = str(api_error)  # type: ignore
            raise ProviderAPIError(msg) from api_error
        except Exception as exc:
            msg = str(exc)
            raise ProviderError(
                message=msg,
                provider_type="perplexity",
                details={"error": str(exc)},
            ) from exc
