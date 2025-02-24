"""Message types for the event system.

This module provides message type definitions for the event system.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pepperpy.core.models import BaseModel, Field


class MessageType(str, Enum):
    """Message type enumeration."""

    # System messages
    SYSTEM = "system"
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"

    # Component messages
    COMPONENT = "component"
    COMPONENT_CREATED = "component.created"
    COMPONENT_INITIALIZED = "component.initialized"
    COMPONENT_ERROR = "component.error"
    COMPONENT_CLEANED = "component.cleaned"

    # Agent messages
    AGENT = "agent"
    AGENT_CREATED = "agent.created"
    AGENT_REMOVED = "agent.removed"
    AGENT_STATE_CHANGED = "agent.state.changed"

    # Workflow messages
    WORKFLOW = "workflow"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Resource messages
    RESOURCE = "resource"
    RESOURCE_CREATED = "resource.created"
    RESOURCE_UPDATED = "resource.updated"
    RESOURCE_DELETED = "resource.deleted"

    # Security messages
    SECURITY = "security"
    SECURITY_AUTH = "security.auth"
    SECURITY_AUTHZ = "security.authz"
    SECURITY_ERROR = "security.error"


class MessagePriority(str, Enum):
    """Message priority enumeration."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Message(BaseModel):
    """Base message model."""

    id: UUID = Field(default_factory=uuid4, description="Message ID")
    type: MessageType = Field(description="Message type")
    source: str = Field(description="Message source")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID | None = Field(default=None)
    reply_to: str | None = Field(default=None)


class SystemMessage(Message):
    """System message model."""

    type: MessageType = Field(
        default=MessageType.SYSTEM,
        description="System message type",
    )
    component: str = Field(description="System component")
    action: str = Field(description="System action")
    status: str = Field(description="System status")


class ComponentMessage(Message):
    """Component message model."""

    type: MessageType = Field(
        default=MessageType.COMPONENT,
        description="Component message type",
    )
    component_id: str = Field(description="Component ID")
    component_type: str = Field(description="Component type")
    state: str = Field(description="Component state")


class AgentMessage(Message):
    """Agent message model."""

    type: MessageType = Field(
        default=MessageType.AGENT,
        description="Agent message type",
    )
    agent_id: str = Field(description="Agent ID")
    agent_type: str = Field(description="Agent type")
    state: str = Field(description="Agent state")


class WorkflowMessage(Message):
    """Workflow message model."""

    type: MessageType = Field(
        default=MessageType.WORKFLOW,
        description="Workflow message type",
    )
    workflow_id: str = Field(description="Workflow ID")
    workflow_type: str = Field(description="Workflow type")
    state: str = Field(description="Workflow state")
    result: dict[str, Any] | None = Field(default=None)
    error: str | None = Field(default=None)


class ResourceMessage(Message):
    """Resource message model."""

    type: MessageType = Field(
        default=MessageType.RESOURCE,
        description="Resource message type",
    )
    resource_id: str = Field(description="Resource ID")
    resource_type: str = Field(description="Resource type")
    action: str = Field(description="Resource action")


class SecurityMessage(Message):
    """Security message model."""

    type: MessageType = Field(
        default=MessageType.SECURITY,
        description="Security message type",
    )
    user_id: str = Field(description="User ID")
    action: str = Field(description="Security action")
    status: str = Field(description="Security status")
    error: str | None = Field(default=None)


# Export public API
__all__ = [
    "AgentMessage",
    "ComponentMessage",
    "Message",
    "MessagePriority",
    "MessageType",
    "ResourceMessage",
    "SecurityMessage",
    "SystemMessage",
    "WorkflowMessage",
]
