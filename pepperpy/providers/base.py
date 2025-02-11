"""Base provider interface for the Pepperpy framework.

This module defines the core interfaces and base classes that all providers
must implement, ensuring consistent behavior across different implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from types import TracebackType
from typing import (
    Any,
    Dict,
    List,
    NotRequired,
    Optional,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ConfigDict, SecretStr

from pepperpy.core.errors import ValidationError
from pepperpy.core.types import Message, Response
from pepperpy.monitoring import bind_logger, logger
from pepperpy.providers.domain import (
    ProviderError,
)

T = TypeVar("T", covariant=True)

# Valid provider types
VALID_PROVIDER_TYPES = frozenset(
    {
        "openai",
        "anthropic",
        "openrouter",
        "local",
        "stackspot",
    }
)

# Configure logger
logger = bind_logger(module="providers.base")


class LogContext(TypedDict, total=True):
    """Type definition for logging context information."""

    error: NotRequired[str | Exception]
    status: NotRequired[str]
    model: NotRequired[str]
    provider: NotRequired[str]
    duration: NotRequired[float]
    tokens: NotRequired[int]
    request_id: NotRequired[str]
    extra: NotRequired[Dict[str, Union[str, int, float, bool]]]


class Message(TypedDict):
    """Message type for chat completion."""

    role: str
    content: str


class LoggerProtocol(Protocol):
    """Protocol for logger interface."""

    def error(self, message: str, **context: str) -> None:
        """Log an error message.

        Args:
        ----
            message: The error message to log.
            **context: Additional context information as string values.

        """
        ...

    def info(self, message: str, **context: str) -> None:
        """Log an info message.

        Args:
        ----
            message: The info message to log.
            **context: Additional context information as string values.

        """
        ...

    def debug(self, message: str, **context: str) -> None:
        """Log a debug message.

        Args:
        ----
            message: The debug message to log.
            **context: Additional context information as string values.

        """
        ...

    def warning(self, message: str, **context: str) -> None:
        """Log a warning message.

        Args:
        ----
            message: The warning message to log.
            **context: Additional context information as string values.

        """
        ...


# Type alias for provider configuration values
type ProviderConfigValue = str | int | float | bool | list[str] | dict[str, Any]


class ExtraConfig(TypedDict, total=False):
    """Additional provider configuration options."""

    model_params: NotRequired[dict[str, ProviderConfigValue]]
    api_params: NotRequired[dict[str, ProviderConfigValue]]
    custom_settings: NotRequired[dict[str, ProviderConfigValue]]


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    provider_type: str = "openai"
    api_key: SecretStr | None = None
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 30
    max_retries: int = 3

    model_config = ConfigDict(
        frozen=True,
        extra="allow",
    )


class GenerateKwargs(TypedDict, total=False):
    """Keyword arguments for generate method."""

    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    stop: NotRequired[list[str]]
    stop_sequences: NotRequired[list[str]]
    presence_penalty: NotRequired[float]
    frequency_penalty: NotRequired[float]
    top_p: NotRequired[float]
    top_k: NotRequired[int]


class ProviderKwargs(TypedDict, total=False):
    """Type definition for provider-specific keyword arguments."""

    model: str
    temperature: float
    max_tokens: int
    stop: list[str] | None
    stop_sequences: list[str] | None


class EmbeddingKwargs(TypedDict, total=False):
    """Keyword arguments for embedding methods."""

    model: NotRequired[str]
    model_params: NotRequired[dict[str, Any]]
    batch_size: NotRequired[int]
    encoding_format: NotRequired[str]


class StreamKwargs(TypedDict, total=False):
    """Keyword arguments for stream method."""

    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    stop: NotRequired[list[str]]
    chunk_size: NotRequired[int]
    buffer_size: NotRequired[int]


class BaseProvider(ABC):
    """Base class for all providers.

    All providers must inherit from this class and implement its abstract methods
    to ensure consistent behavior across different implementations.

    Attributes
    ----------
        config (ProviderConfig): Provider configuration
        name (str): Provider name (class name)
        _initialized (bool): Whether the provider is initialized
        _logger (LoggerProtocol): Logger instance with context support

    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider with configuration.

        Args:
        ----
            config: Provider configuration

        """
        self.config = config
        self.name = self.__class__.__name__
        self._initialized = False
        self._logger = bind_logger(provider=self.name)

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider.

        Raises
        ------
            ValidationError: If provider is already initialized

        """
        if self._initialized:
            raise ValidationError("Provider already initialized")
        self._initialized = True
        self._logger.info("Provider initialized successfully")

    async def cleanup(self) -> None:
        """Clean up provider resources.

        Raises
        ------
            ValidationError: If provider is not initialized

        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")
        self._initialized = False
        self._logger.info("Provider cleaned up successfully")

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized.

        Raises
        ------
            ValidationError: If provider is not initialized

        """
        if not self._initialized:
            raise ValidationError("Provider not initialized")

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        kwargs: ProviderKwargs | None = None,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the provider.

        Args:
        ----
            prompt: The prompt to complete
            kwargs: Additional provider-specific parameters

        Returns:
        -------
            Generated text or async generator of text chunks if streaming

        Raises:
        ------
            ValidationError: If provider is not initialized
            ProviderError: If text generation fails

        """
        raise NotImplementedError

    @abstractmethod
    async def generate(
        self, messages: list[Message], **kwargs: GenerateKwargs
    ) -> Response:
        """Generate a response from the provider.

        Args:
        ----
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the provider

        Returns:
        -------
            Generated response

        Raises:
        ------
            ProviderInitError: If the provider is not initialized
            ProviderAPIError: If the API request fails
            ProviderError: If generation fails for other reasons

        """
        self._ensure_initialized()
        raise NotImplementedError

    @abstractmethod
    def stream(
        self, messages: list[Message], **kwargs: StreamKwargs
    ) -> AsyncIterator[Response]:
        """Stream responses from the provider.

        Args:
        ----
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the provider

        Returns:
        -------
            AsyncIterator[Response]: Stream of responses

        Raises:
        ------
            ProviderInitError: If the provider is not initialized
            ProviderAPIError: If the API request fails
            ProviderError: If streaming fails for other reasons

        """
        self._ensure_initialized()
        raise NotImplementedError

    def _stringify_context(
        self, context: dict[str, str | int | float | bool]
    ) -> dict[str, str]:
        """Convert all context values to strings.

        Args:
        ----
            context: Dictionary with mixed-type values

        Returns:
        -------
            Dictionary with all string values

        """
        return {k: str(v) for k, v in context.items()}

    async def _handle_api_error(
        self, error: Exception, context: dict[str, str | int | float | bool]
    ) -> None:
        """Handle API errors in a consistent way.

        Args:
        ----
            error: The original error
            context: Additional context about the error

        Raises:
        ------
            ProviderError: With appropriate error details

        """
        log_context = self._stringify_context(
            {
                "error": str(error),
                "provider": self.name,
                **context,
            }
        )
        self._logger.error("API error occurred", **log_context)
        raise ProviderError(
            message=str(error), provider_type=self.name, details=context
        ) from error

    def _check_initialized(self) -> None:
        """Check if provider is initialized.

        Raises
        ------
            RuntimeError: If provider is not initialized

        """
        if not self._initialized:
            raise RuntimeError(
                f"Provider {self.name} not initialized. Call initialize() first."
            )

    async def __aenter__(self) -> "BaseProvider":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.cleanup()

    @abstractmethod
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

        """
        raise NotImplementedError


class Provider(ABC):
    """Base class for AI providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider.

        Args:
        ----
            config: Optional configuration for the provider.

        """
        self.config = config or {}

    @abstractmethod
    async def generate(
        self, prompt: str, parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response for the given prompt.

        Args:
        ----
            prompt: The prompt to generate a response for.
            parameters: Optional parameters for the generation.

        Returns:
        -------
            The generated response.

        """
        pass
