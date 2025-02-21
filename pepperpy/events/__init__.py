"""Event system for the Pepperpy framework.

This module provides a comprehensive event system with:
- Event bus implementation
- Event handlers and callbacks
- Event prioritization
- Event filtering
- Lifecycle hooks
"""

from pepperpy.events.base import (
    Event,
    EventBus,
    EventEmitter,
    EventFilter,
    EventHandler,
    EventMetrics,
    EventPriority,
    EventType,
)
from pepperpy.events.handlers import (
    AgentCreatedEvent,
    AgentEventHandler,
    AgentRemovedEvent,
    AgentStateChangedEvent,
    HubAssetCreatedEvent,
    HubAssetDeletedEvent,
    HubAssetUpdatedEvent,
    HubEventHandler,
    MemoryEventHandler,
    MemoryRetrievedEvent,
    MemoryStoredEvent,
    MemoryUpdatedEvent,
    WorkflowCompletedEvent,
    WorkflowEventHandler,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)
from pepperpy.events.hooks import (
    HookCallback,
    HookManager,
    hook_manager,
)

__all__ = [
    # Base event system
    "Event",
    "EventBus",
    "EventEmitter",
    "EventFilter",
    "EventHandler",
    "EventMetrics",
    "EventPriority",
    "EventType",
    # Agent events
    "AgentCreatedEvent",
    "AgentRemovedEvent",
    "AgentStateChangedEvent",
    "AgentEventHandler",
    # Hub events
    "HubAssetCreatedEvent",
    "HubAssetUpdatedEvent",
    "HubAssetDeletedEvent",
    "HubEventHandler",
    # Memory events
    "MemoryStoredEvent",
    "MemoryRetrievedEvent",
    "MemoryUpdatedEvent",
    "MemoryEventHandler",
    # Workflow events
    "WorkflowStartedEvent",
    "WorkflowCompletedEvent",
    "WorkflowFailedEvent",
    "WorkflowEventHandler",
    # Hook system
    "HookCallback",
    "HookManager",
    "hook_manager",
]
