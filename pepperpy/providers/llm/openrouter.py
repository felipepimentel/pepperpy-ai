"""OpenRouter provider implementation for the Pepperpy framework.

This module provides integration with OpenRouter's API, supporting both chat completion
and streaming capabilities.
"""

import os
from collections.abc import AsyncGenerator, Sequence
from typing import TypeAlias, TypeVar, Union

from openai import AsyncOpenAI, AsyncStream, OpenAIError
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
from pydantic import ConfigDict, Field, SecretStr, field_validator

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
            config.config.get("api_key", "")
            if config.config
            else os.getenv("PEPPERPY_API_KEY", "")
        )

        # Convert to OpenRouterConfig if needed
        openrouter_config = (
            config
            if isinstance(config, OpenRouterConfig)
            else OpenRouterConfig(
                type="openrouter",
                config={
                    **config.config,
                    "api_key": SecretStr(api_key),
                },
            )
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
                message=msg, provider_type="openrouter", details={"error": str(exc)}
            ) from exc

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            try:
                await self._client.close()
                self._client = None
                await super().cleanup()
                self._initialized = False
                logger.info("Cleaned up OpenRouter provider")
            except Exception as exc:  # type: ignore
                logger.error(f"Error during cleanup: {exc!r}")
                raise ProviderError(
                    message=f"Cleanup failed: {exc}",
                    provider_type="openrouter",
                    details={"error": str(exc)},
                ) from exc

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
                raise ProviderError("OpenRouter client not initialized")

            # Convert message to OpenRouter format
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

    async def _stream_response(
        self, response: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[ProviderResponse, None]:
        """Stream response chunks.

        Args:
            response: OpenRouter response stream

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
