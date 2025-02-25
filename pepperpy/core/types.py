"""Core type definitions for the Pepperpy framework.

This module provides core type definitions used throughout the framework.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Any
from uuid import UUID, uuid4

from pepperpy.core.models import BaseModel, ConfigDict, Field


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
        type: MessageType
        content: MessageContent
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

    id: UUID = Field(default_factory=uuid4, description="Message ID")
    type: MessageType = Field(description="Message type")
    content: MessageContent = Field(description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp",
    )


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


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ComponentState(Enum):
    """Component lifecycle states."""

    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    EXECUTING = auto()
    CLEANING = auto()
    CLEANED = auto()
    ERROR = auto()


__all__ = [
    "AgentState",
    "ComponentState",
    "Message",
    "MessageContent",
    "MessageType",
    "Response",
]
