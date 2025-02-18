"""Base provider implementation.

This module provides the base provider class that all providers must inherit from.
It defines the core functionality and interface that all Pepperpy providers
must implement.
"""

from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import NotRequired

from pepperpy.core.base import BaseComponent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger

from .domain import (
    ProviderCapability,
    ProviderConfig,
    ProviderMetadata,
    ProviderState,
)
from .types import ProviderMessage, ProviderResponse

logger = get_logger(__name__)

T = TypeVar("T", covariant=True)

# Type alias for provider callback
ProviderCallback = Callable[[Dict[str, Any]], None]

# Valid provider types
VALID_PROVIDER_TYPES = frozenset({
    "services.openai",
    "services.openrouter",
    "services.anthropic",
    "services.gemini",
    "services.perplexity",
    "services.stackspot",
})

# Configure logger
logger = get_logger(__name__)


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


class Message(BaseModel):
    """A message that can be exchanged with providers."""

    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class Response(BaseModel):
    """A response from a provider."""

    id: UUID
    content: str
    metadata: Optional[Dict[str, Any]] = None


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


class GenerateKwargs(BaseModel):
    """Keyword arguments for generate method."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    stop_sequences: Optional[List[str]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


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


class StreamKwargs(BaseModel):
    """Keyword arguments for stream method."""

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    chunk_size: Optional[int] = None
    buffer_size: Optional[int] = None


class BaseProvider(BaseComponent):
    """Base class for all Pepperpy providers.

    This class provides the foundation for building providers in the Pepperpy
    framework. It handles lifecycle management, state tracking, and basic
    provider functionality.

    Attributes:
        id: Unique identifier for the provider
        state: Current provider state
        metadata: Provider metadata
        config: Provider configuration
        capabilities: List of provider capabilities

    """

    def __init__(
        self,
        id: UUID,
        metadata: Optional[ProviderMetadata] = None,
        config: Optional[ProviderConfig] = None,
    ) -> None:
        """Initialize the base provider.

        Args:
            id: Unique identifier for the provider
            metadata: Optional provider metadata
            config: Optional provider configuration

        Raises:
            ConfigurationError: If configuration is invalid

        """
        super().__init__(id, metadata)
        self.config = config or ProviderConfig(
            provider_type="base",
            name="base",
            version="1.0.0",
        )
        self.state = ProviderState.CREATED
        self._logger = logger.getChild(self.__class__.__name__)

    @property
    def capabilities(self) -> List[ProviderCapability]:
        """Get provider capabilities.

        Returns:
            List of capability identifiers

        """
        return []

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called during provider startup to perform any necessary
        initialization.

        Raises:
            StateError: If provider is in invalid state
            ConfigurationError: If initialization fails

        """
        if self.state != ProviderState.CREATED:
            raise StateError(f"Cannot initialize provider in state: {self.state}")

        try:
            self.state = ProviderState.INITIALIZING
            # Perform initialization
            self.state = ProviderState.READY
        except Exception as e:
            self.state = ProviderState.ERROR
            raise ConfigurationError(f"Provider initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called during provider shutdown to perform cleanup.
        """
        if self.state not in {ProviderState.READY, ProviderState.ERROR}:
            raise StateError(f"Cannot cleanup provider in state: {self.state}")

        try:
            self.state = ProviderState.CLEANING
            # Perform cleanup
            self.state = ProviderState.TERMINATED
        except Exception as e:
            self.state = ProviderState.ERROR
            raise StateError(f"Provider cleanup failed: {e}") from e

    @abstractmethod
    async def process_message(self, message: ProviderMessage) -> ProviderResponse[Any]:
        """Process an incoming message.

        This is the main entry point for provider message processing. All providers
        must implement this method to handle incoming messages.

        Args:
            message: The message to process

        Returns:
            Response containing processing results

        Raises:
            NotImplementedError: If not implemented by subclass

        """
        raise NotImplementedError

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the provider's main functionality.

        This method implements the BaseComponent interface. It processes
        a message if one is provided in kwargs.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution results

        Raises:
            StateError: If provider is in invalid state

        """
        if self.state != ProviderState.READY:
            raise StateError(f"Cannot execute provider in state: {self.state}")

        message = kwargs.get("message")
        if not message:
            raise ConfigurationError("Message is required for execution")

        try:
            self.state = ProviderState.PROCESSING
            response = await self.process_message(message)
            self.state = ProviderState.READY
            return response
        except Exception as e:
            self.state = ProviderState.ERROR
            raise StateError(f"Provider execution failed: {e}") from e

    def validate(self) -> None:
        """Validate provider state and configuration.

        Raises:
            StateError: If provider state is invalid
            ConfigurationError: If configuration is invalid

        """
        super().validate()
        if not isinstance(self.state, ProviderState):
            raise StateError(f"Invalid provider state: {self.state}")
        if not isinstance(self.config, ProviderConfig):
            raise ConfigurationError(
                "Provider config must be a ProviderConfig instance"
            )


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
