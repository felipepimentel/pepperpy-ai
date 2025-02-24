"""Events package for the Pepperpy framework.

This package provides a unified event system with support for:
- Event registration and dispatch
- Event handlers and listeners
- Event filtering and routing
- Event metrics and monitoring
"""

from pepperpy.events.base import Event, EventHandler, EventListener, EventManager
from pepperpy.events.handlers.agent import AgentEventHandler
from pepperpy.events.handlers.workflow import WorkflowEventHandler
from pepperpy.events.listeners.metrics import MetricsListener
from pepperpy.events.messages.types import (
    AgentMessage,
    ComponentMessage,
    Message,
    MessagePriority,
    MessageType,
    ResourceMessage,
    SecurityMessage,
    SystemMessage,
    WorkflowMessage,
)

# Export public API
__all__ = [
    # Base
    "Event",
    "EventHandler",
    "EventListener",
    "EventManager",
    # Handlers
    "AgentEventHandler",
    "WorkflowEventHandler",
    # Listeners
    "MetricsListener",
    # Messages
    "Message",
    "MessageType",
    "MessagePriority",
    "SystemMessage",
    "ComponentMessage",
    "AgentMessage",
    "WorkflowMessage",
    "ResourceMessage",
    "SecurityMessage",
]
