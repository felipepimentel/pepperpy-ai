"""Provider types module."""

from enum import Enum
from typing import Protocol, TypedDict, TypeVar

T = TypeVar("T")
SafeType = TypeVar("SafeType", str, int, bool)


def safe_str(value: str | int | float | bool | None, default: str = "") -> str:
    """Safely convert value to string."""
    return str(value) if value is not None else default


def safe_int(value: str | int | float | None, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        return int(float(value)) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_bool(value: str | int | float | bool | None, default: bool = False) -> bool:
    """Safely convert value to bool."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return default


def safe_str_or_none(value: str | int | float | bool | None) -> str | None:
    """Safely convert value to string or None."""
    return str(value) if value is not None else None


class ProviderType(str, Enum):
    """Provider types.

    Supported AI provider types.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    STACKSPOT = "stackspot"
    OPENROUTER = "openrouter"
    MOCK = "mock"

    @classmethod
    def from_str(cls, value: str) -> "ProviderType":
        """Create from string.

        Args:
            value: Provider type string

        Returns:
            Provider type

        Raises:
            ValueError: If value is invalid
        """
        try:
            return cls(value.lower())
        except ValueError as err:
            raise ValueError(
                f"Invalid provider type: {value}. "
                f"Supported types: {', '.join(cls.__members__.keys())}"
            ) from err


class Capabilities(TypedDict):
    """Provider capabilities dictionary."""

    streaming: bool
    chat: bool
    embeddings: bool
    images: bool
    audio: bool
    vision: bool


class ProviderMetadata(Protocol):
    """Provider metadata.

    Attributes:
        name: Provider name
        description: Provider description
        version: Provider version
        capabilities: Provider capabilities
    """

    name: str
    description: str
    version: str
    capabilities: Capabilities


class ProviderResponse(Protocol):
    """Provider response.

    Attributes:
        content: Response content
        model: Model used for generation
        provider: Provider name
        metadata: Additional metadata
    """

    content: str
    model: str | None
    provider: str
    metadata: dict[str, str | int | float | bool | None]


class ProviderUsage:
    """Provider usage statistics.

    Attributes:
        total_tokens: Total tokens used
        prompt_tokens: Prompt tokens used
        completion_tokens: Completion tokens used
        total_cost: Total cost in USD
    """

    def __init__(
        self,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_cost: float = 0.0,
    ) -> None:
        """Initialize usage statistics.

        Args:
            total_tokens: Total tokens used
            prompt_tokens: Prompt tokens used
            completion_tokens: Completion tokens used
            total_cost: Total cost in USD
        """
        self.total_tokens = total_tokens
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_cost = total_cost


class ProviderError(Exception):
    """Base class for provider errors."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize provider error.

        Args:
            message: Error message.
            provider: Provider name.
            operation: Operation that failed.
            cause: Original exception.
        """
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.cause = cause
