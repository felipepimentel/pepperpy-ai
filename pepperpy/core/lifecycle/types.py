"""Lifecycle types module for the Pepperpy framework.

This module defines core lifecycle types used throughout the framework.
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class LifecycleState(str, Enum):
    """Component lifecycle states."""

    UNREGISTERED = "unregistered"  # Initial state before registration
    CREATED = "created"  # Component created but not initialized
    INITIALIZING = "initializing"  # Component is being initialized
    READY = "ready"  # Component is initialized and ready
    RUNNING = "running"  # Component is actively running
    STOPPING = "stopping"  # Component is being stopped
    STOPPED = "stopped"  # Component is stopped but can be restarted
    CLEANING = "cleaning"  # Component is being cleaned up
    CLEANED = "cleaned"  # Component is cleaned and cannot be reused
    ERROR = "error"  # Component is in error state


@dataclass
class LifecycleMetadata:
    """Metadata for lifecycle management."""

    component_id: str  # Unique identifier for the component
    component_type: str  # Type/class name of the component
    state: LifecycleState  # Current lifecycle state
    created_at: datetime  # Creation timestamp
    updated_at: datetime  # Last update timestamp
    error: str | None = None  # Last error message if any
    dependencies: list[str] | None = None  # List of component dependencies
    metrics: dict[str, Any] | None = None  # Component-specific metrics

    def __post_init__(self):
        """Initialize default values."""
        if self.dependencies is None:
            self.dependencies = []
        if self.metrics is None:
            self.metrics = {}


@dataclass
class StateTransition:
    """State transition definition."""

    from_state: LifecycleState  # Source state
    to_state: LifecycleState  # Target state
    timestamp: datetime  # When the transition occurred
    description: str = ""  # Optional transition description
    metadata: dict[str, Any] | None = None  # Additional transition metadata

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class Lifecycle(Protocol):
    """Protocol for components with lifecycle management."""

    @property
    @abstractmethod
    def metadata(self) -> LifecycleMetadata:
        """Get component metadata."""
        ...

    @property
    @abstractmethod
    def state(self) -> LifecycleState:
        """Get current lifecycle state."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        It should set up any necessary resources and put the component
        in a ready state.

        Raises:
            LifecycleError: If initialization fails
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the component.

        This method should be called to start the component's main functionality.
        It should transition the component from READY to RUNNING state.

        Raises:
            LifecycleError: If start fails
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the component.

        This method should be called to stop the component's main functionality.
        It should transition the component from RUNNING to STOPPED state.

        Raises:
            LifecycleError: If stop fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be called when the component is no longer needed.
        It should release any resources and put the component in a cleaned state.

        Raises:
            LifecycleError: If cleanup fails
        """
        ...


# Valid state transitions
VALID_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.UNREGISTERED: {LifecycleState.CREATED, LifecycleState.ERROR},
    LifecycleState.CREATED: {LifecycleState.INITIALIZING, LifecycleState.ERROR},
    LifecycleState.INITIALIZING: {LifecycleState.READY, LifecycleState.ERROR},
    LifecycleState.READY: {
        LifecycleState.RUNNING,
        LifecycleState.CLEANING,
        LifecycleState.ERROR,
    },
    LifecycleState.RUNNING: {LifecycleState.STOPPING, LifecycleState.ERROR},
    LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.ERROR},
    LifecycleState.STOPPED: {
        LifecycleState.RUNNING,
        LifecycleState.CLEANING,
        LifecycleState.ERROR,
    },
    LifecycleState.CLEANING: {LifecycleState.CLEANED, LifecycleState.ERROR},
    LifecycleState.CLEANED: {LifecycleState.ERROR},
    LifecycleState.ERROR: {
        LifecycleState.INITIALIZING,
        LifecycleState.RUNNING,
        LifecycleState.STOPPING,
        LifecycleState.CLEANING,
    },
}


# Export public API
__all__ = [
    "VALID_TRANSITIONS",
    "Lifecycle",
    "LifecycleMetadata",
    "LifecycleState",
    "StateTransition",
]
