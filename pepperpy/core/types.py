"""Core type definitions.

This module provides core type definitions used throughout the project.
"""

from enum import Enum
from typing import NewType, TypeVar

# Core types
UserId = NewType("UserId", str)
ResourceId = NewType("ResourceId", str)
PluginId = NewType("PluginId", str)
WorkflowId = NewType("WorkflowId", str)
AgentId = NewType("AgentId", str)
CapabilityId = NewType("CapabilityId", str)
ProviderId = NewType("ProviderId", str)

# Generic types
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Result types
Result = TypeVar("Result")
Error = TypeVar("Error")

# Type aliases
WorkflowID = WorkflowId  # For backward compatibility


class ComponentState(str, Enum):
    """Component states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    FINALIZED = "finalized"


class AgentState(str, Enum):
    """Agent states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    FINALIZED = "finalized"


__all__ = [
    # Core types
    "UserId",
    "ResourceId",
    "PluginId",
    "WorkflowId",
    "WorkflowID",  # Alias
    "AgentId",
    "CapabilityId",
    "ProviderId",
    # Generic types
    "T",
    "K",
    "V",
    # Result types
    "Result",
    "Error",
    # Enums
    "ComponentState",
    "AgentState",
] 