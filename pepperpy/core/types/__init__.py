"""Type definitions for the Pepperpy framework.

This module provides core type definitions used throughout the framework.
It includes type aliases and common types.

Status: Stable
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Any, Protocol, Union, runtime_checkable
from uuid import UUID

from pepperpy.core.models import BaseModel, ConfigDict, Field

# Type aliases
AgentID = UUID
MessageID = UUID
WorkflowID = UUID
ResourceID = UUID
CapabilityID = UUID
ProviderID = UUID

# Common types
MetadataValue = Union[str, int, float, bool, None]
MetadataDict = dict[str, MetadataValue]


@runtime_checkable
class Lifecycle(Protocol):
    """Protocol for components with lifecycle management."""

    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        It should set up any necessary resources and put the component
        in a ready state.

        Raises:
            LifecycleError: If initialization fails
        """
        ...

    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be called when the component is no longer needed.
        It should release any resources and put the component in a cleaned state.

        Raises:
            LifecycleError: If cleanup fails
        """
        ...


class MessageType(Enum):
    """Types of messages that can be exchanged."""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    FUNCTION = auto()
    ERROR = auto()


class MessageContent(BaseModel):
    """Content of a message.

    Attributes:
        text: Text content of the message
        metadata: Additional metadata
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    text: str = Field(description="Text content of the message")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class Message(BaseModel):
    """Message exchanged between components.

    Attributes:
        id: Message ID
        type: Message type
        content: Message content
        timestamp: Message timestamp
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: MessageID = Field(description="Message ID")
    type: MessageType = Field(description="Message type")
    content: MessageContent = Field(description="Message content")
    timestamp: datetime = Field(description="Message timestamp")


class Response(BaseModel):
    """Response from a component.

    Attributes:
        message: Response message
        metadata: Additional metadata
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    message: Message = Field(description="Response message")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class ComponentState(Enum):
    """States a component can be in."""

    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    ERROR = auto()
    CLEANING = auto()
    CLEANED = auto()
    EXECUTING = auto()


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


__all__ = [
    # Type aliases
    "AgentID",
    "MessageID",
    "WorkflowID",
    "ResourceID",
    "CapabilityID",
    "ProviderID",
    # Common types
    "MetadataValue",
    "MetadataDict",
    # Enums
    "MessageType",
    # Models
    "MessageContent",
    "Message",
    "Response",
    "ComponentState",
    "AgentState",
    # Protocols
    "Lifecycle",
]
