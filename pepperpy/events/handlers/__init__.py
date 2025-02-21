"""Event handlers for the Pepperpy framework.

This module provides event handlers for:
- Agent events
- Workflow events
- Memory events
- Hub events
"""

from pepperpy.events.handlers.agent_events import (
    AgentCreatedEvent,
    AgentEventHandler,
    AgentRemovedEvent,
    AgentStateChangedEvent,
)
from pepperpy.events.handlers.hub_events import (
    HubAssetCreatedEvent,
    HubAssetDeletedEvent,
    HubAssetUpdatedEvent,
    HubEventHandler,
)
from pepperpy.events.handlers.memory_events import (
    MemoryEventHandler,
    MemoryRetrievedEvent,
    MemoryStoredEvent,
    MemoryUpdatedEvent,
)
from pepperpy.events.handlers.workflow_events import (
    WorkflowCompletedEvent,
    WorkflowEventHandler,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)

__all__ = [
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
]
