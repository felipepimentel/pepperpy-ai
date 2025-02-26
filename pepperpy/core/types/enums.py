"""
Core enums module defining state and type enumerations.

This module provides enumerations for various states and types used
throughout PepperPy.
"""

from enum import Enum, auto
from typing import NewType
from uuid import UUID


class ComponentState(Enum):
    """States that a component can be in."""

    UNKNOWN = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()
    CLEANING = auto()
    CLEANED = auto()


class AgentState(Enum):
    """States that an agent can be in."""

    UNKNOWN = auto()
    INITIALIZING = auto()
    READY = auto()
    EXECUTING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()


# Type aliases for IDs
AgentID = NewType("AgentID", UUID)
CapabilityID = NewType("CapabilityID", UUID)
ResourceID = NewType("ResourceID", UUID)
WorkflowID = NewType("WorkflowID", UUID)


# Export all types
__all__ = [
    "ComponentState",
    "AgentState",
    "AgentID",
    "CapabilityID",
    "ResourceID",
    "WorkflowID",
]
