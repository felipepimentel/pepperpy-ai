"""Core type definitions.

This module provides core type definitions used throughout the framework.
"""

from enum import Enum
from typing import NewType


class ComponentState(str, Enum):
    """Component lifecycle states.

    Attributes:
        CREATED: Component has been created but not initialized
        INITIALIZING: Component is being initialized
        READY: Component is ready for use
        EXECUTING: Component is executing an operation
        ERROR: Component is in error state
        CLEANING: Component is cleaning up resources
        CLEANED: Component has been cleaned up
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    ERROR = "error"
    CLEANING = "cleaning"
    CLEANED = "cleaned"


class AgentState(str, Enum):
    """Agent lifecycle states.

    Attributes:
        CREATED: Agent has been created
        INITIALIZING: Agent is initializing
        READY: Agent is ready
        RUNNING: Agent is running
        PAUSED: Agent is paused
        ERROR: Agent is in error state
        STOPPED: Agent has been stopped
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


# Type aliases for IDs
AgentID = NewType("AgentID", str)
ProviderID = NewType("ProviderID", str)
ResourceID = NewType("ResourceID", str)
CapabilityID = NewType("CapabilityID", str)
WorkflowID = NewType("WorkflowID", str)
ComponentID = NewType("ComponentID", str)


# Export public API
__all__ = [
    "AgentID",
    "AgentState",
    "CapabilityID",
    "ComponentID",
    "ComponentState",
    "ProviderID",
    "ResourceID",
    "WorkflowID",
]
