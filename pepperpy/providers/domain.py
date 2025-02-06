"""Domain models and errors for the provider system.

This module defines the core domain models and error types used by providers.
It includes message and conversation models, as well as a hierarchy of
provider-specific exceptions.

Example:
    >>> from pepperpy.providers.domain import Message, Conversation
    >>> message = Message(role="user", content="Hello!")
    >>> conversation = Conversation()
    >>> conversation.add_message("user", "Hello!")
"""

from datetime import datetime
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pepperpy.common.errors import PepperpyError
from pepperpy.monitoring import logger

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
        default_factory=datetime.utcnow,
        description="When the message was created (UTC)",
    )
    metadata: dict[str, Any] = Field(
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
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional conversation metadata"
    )

    def add_message(self, role: str, content: str, **metadata: Any) -> None:
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
    """Base class for provider errors."""

    def __init__(
        self,
        message: str,
        provider_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            provider_type: Type of provider that raised the error
            details: Additional error details
        """
        super().__init__(message)
        error_msg = (
            f"Provider error occurred: {message} "
            f"(provider: {provider_type}, details: {details or {}})"
        )
        logger.error(message=error_msg)
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
