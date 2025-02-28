"""Domain models and errors for the provider system.

This module defines the core domain models and error types used by providers.
It includes message and conversation models, as well as a hierarchy of
provider-specific exceptions.

Example:
    >>> from pepperpy.agents.providers.domain import Message, Conversation
    >>> message = Message(role="user", content="Hello!")
    >>> conversation = Conversation()
    >>> conversation.add_message("user", "Hello!")

"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pepperpy.common.base import Metadata
from pepperpy.core.errors import PepperpyError
from pepperpy.common.logging import get_logger
from pepperpy.core.types import MetadataDict, MetadataValue

logger = get_logger(__name__)

# Message roles
ROLE_SYSTEM: Final[str] = "system"
ROLE_USER: Final[str] = "user"
ROLE_ASSISTANT: Final[str] = "assistant"
ROLE_FUNCTION: Final[str] = "function"

VALID_ROLES: Final[list[str]] = [
    ROLE_SYSTEM,
    ROLE_USER,
    ROLE_ASSISTANT,
    ROLE_FUNCTION,
]


class Message(BaseModel):
    """A message in a conversation.

    Attributes:
        role: Role of the message sender (e.g., 'user', 'assistant')
        content: Content of the message
        timestamp: When the message was created (UTC)
        metadata: Additional message metadata
        name: Optional name for function messages

    Example:
        >>> message = Message(
        ...     role="user",
        ...     content="Hello!",
        ...     metadata={"source": "chat"}
        ... )

    """

    role: str
    content: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the message was created (UTC)",
    )
    metadata: MetadataDict = Field(
        default_factory=dict, description="Additional message metadata"
    )
    name: str | None = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate the message role.

        Args:
            v: The role value to validate

        Returns:
            The validated role

        Raises:
            ValueError: If role is invalid

        Example:
            >>> message = Message(role="invalid", content="test")
            ValueError: Invalid role: invalid

        """
        if v not in VALID_ROLES:
            raise ValueError(f"Invalid role: {v}")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate the message content.

        Args:
            v: The content value to validate

        Returns:
            The validated content

        Raises:
            ValueError: If content is empty

        Example:
            >>> message = Message(role="user", content="")
            ValueError: Message content cannot be empty

        """
        if not v:
            raise ValueError("Message content cannot be empty")
        return v


class Conversation(BaseModel):
    """A conversation with a provider.

    Attributes:
        messages: List of messages in the conversation
        metadata: Additional conversation metadata

    Example:
        >>> conversation = Conversation()
        >>> conversation.add_message("user", "Hello!")
        >>> assert len(conversation.messages) == 1

    """

    messages: list[Message] = Field(
        default_factory=list, description="List of messages in the conversation"
    )
    metadata: MetadataDict = Field(
        default_factory=dict, description="Additional conversation metadata"
    )

    def add_message(self, role: str, content: str, **metadata: MetadataValue) -> None:
        """Add a message to the conversation.

        Args:
            role: Role of the message sender
            content: Content of the message
            **metadata: Additional message metadata

        Raises:
            ValueError: If role is invalid or content is empty

        Example:
            >>> conversation.add_message(
            ...     "user",
            ...     "Hello!",
            ...     source="chat"
            ... )

        """
        if not content:
            raise ValueError("Message content cannot be empty")

        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)


class ProviderError(PepperpyError):
    """Base class for provider-related errors.

    Attributes:
        provider_type: Type of provider that raised the error
        details: Additional error details

    """

    def __init__(
        self,
        message: str,
        provider_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize provider error.

        Args:
            message: Error message
            provider_type: Type of provider that raised the error
            details: Additional error details

        """
        error_msg = (
            f"Provider error: {message} "
            f"(provider: {provider_type}, details: {details or {}})"
        )
        super().__init__(error_msg)
        logger.error(error_msg)
        self.provider_type = provider_type
        self.details = details or {}


class ProviderNotFoundError(ProviderError):
    """Raised when a provider type is not found.

    Example:
        >>> raise ProviderNotFoundError(
        ...     "Provider 'unknown' not found",
        ...     provider_type="unknown"
        ... )

    """


class ProviderInitError(ProviderError):
    """Raised when provider initialization fails.

    Example:
        >>> raise ProviderInitError(
        ...     "Failed to initialize provider",
        ...     provider_type="openai",
        ...     details={"error": "Invalid API key"}
        ... )

    """


class ProviderConfigError(ProviderError):
    """Raised when provider configuration is invalid.

    Example:
        >>> raise ProviderConfigError(
        ...     "Invalid configuration",
        ...     provider_type="openai",
        ...     details={"field": "api_key"}
        ... )

    """


class ProviderAPIError(ProviderError):
    """Raised when a provider API call fails.

    Example:
        >>> raise ProviderAPIError(
        ...     "API request failed",
        ...     provider_type="openai",
        ...     details={"status": 500}
        ... )

    """


class ProviderRateLimitError(ProviderAPIError):
    """Raised when provider rate limit is exceeded.

    Example:
        >>> raise ProviderRateLimitError(
        ...     "Rate limit exceeded",
        ...     provider_type="openai",
        ...     details={"retry_after": 30}
        ... )

    """


class ProviderAuthError(ProviderAPIError):
    """Raised when provider authentication fails."""

    pass


class ProviderState(str, Enum):
    """Possible states of a provider."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    CLEANING = "cleaning"
    TERMINATED = "terminated"


@dataclass
class ProviderCapability:
    """Provider capability definition."""

    name: str
    version: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderContext:
    """Context for provider execution."""

    provider_id: UUID
    session_id: UUID
    state: ProviderState
    capabilities: list[ProviderCapability]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProviderConfig:
    """Configuration for provider initialization."""

    provider_type: str
    name: str
    version: str
    api_key: str | None = None
    base_url: str | None = None
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderMetadata(Metadata):
    """Metadata specific to providers."""

    provider_type: str
    capabilities: list[str]
    settings: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
