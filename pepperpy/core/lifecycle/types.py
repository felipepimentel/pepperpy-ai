"""Core lifecycle types module.

This module defines the core types used for lifecycle management, including:
- LifecycleState: Enumeration of possible lifecycle states
- Lifecycle: Protocol defining the lifecycle interface
- LifecycleEvent: Events that can occur during lifecycle
- LifecycleConfig: Configuration for lifecycle components
- LifecycleContext: Context for lifecycle operations
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Protocol


class LifecycleState(Enum):
    """Enumeration of possible lifecycle states."""

    UNINITIALIZED = auto()
    CREATED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FINALIZING = auto()
    FINALIZED = auto()
    ERROR = auto()


class LifecycleEvent(Enum):
    """Events that can occur during lifecycle."""

    INITIALIZE = "initialize"
    START = "start"
    STOP = "stop"
    FINALIZE = "finalize"
    ERROR = "error"
    RETRY = "retry"
    TIMEOUT = "timeout"


@dataclass
class LifecycleConfig:
    """Configuration for lifecycle components."""

    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    parallel_operations: bool = True
    strict_mode: bool = True
    error_recovery: bool = True
    metrics_enabled: bool = True
    logging_enabled: bool = True


@dataclass
class LifecycleContext:
    """Context for lifecycle operations."""

    component_id: str
    state: LifecycleState
    event: LifecycleEvent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Exception | None = None


@dataclass
class LifecycleTransition:
    """Represents a transition between lifecycle states."""

    from_state: LifecycleState
    to_state: LifecycleState
    event: LifecycleEvent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LifecycleMetrics:
    """Metrics for lifecycle operations."""

    transitions: list[LifecycleTransition] = field(default_factory=list)
    errors: list[Exception] = field(default_factory=list)
    durations: dict[LifecycleEvent, float] = field(default_factory=dict)
    retries: dict[LifecycleEvent, int] = field(default_factory=dict)


class LifecycleHook(Protocol):
    """Protocol for lifecycle hooks."""

    async def pre_event(self, context: LifecycleContext) -> None:
        """Called before a lifecycle event.

        Args:
            context: Event context

        """
        ...

    async def post_event(self, context: LifecycleContext) -> None:
        """Called after a lifecycle event.

        Args:
            context: Event context

        """
        ...

    async def on_error(self, context: LifecycleContext) -> None:
        """Called when an error occurs.

        Args:
            context: Error context

        """
        ...


class Lifecycle(Protocol):
    """Protocol for lifecycle management."""

    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            LifecycleError: If initialization fails

        """
        ...

    async def start(self) -> None:
        """Start the component.

        Raises:
            LifecycleError: If start fails

        """
        ...

    async def stop(self) -> None:
        """Stop the component.

        Raises:
            LifecycleError: If stop fails

        """
        ...

    async def cleanup(self) -> None:
        """Clean up component resources.

        Raises:
            LifecycleError: If cleanup fails

        """
        ...


# Define allowed state transitions
ALLOWED_TRANSITIONS = {
    LifecycleState.UNINITIALIZED: {
        LifecycleState.INITIALIZING,
        LifecycleState.ERROR,
    },
    LifecycleState.INITIALIZING: {
        LifecycleState.READY,
        LifecycleState.ERROR,
    },
    LifecycleState.READY: {
        LifecycleState.RUNNING,
        LifecycleState.STOPPING,
        LifecycleState.ERROR,
    },
    LifecycleState.RUNNING: {
        LifecycleState.STOPPING,
        LifecycleState.ERROR,
    },
    LifecycleState.STOPPING: {
        LifecycleState.STOPPED,
        LifecycleState.ERROR,
    },
    LifecycleState.STOPPED: {
        LifecycleState.FINALIZING,
        LifecycleState.ERROR,
    },
    LifecycleState.FINALIZING: {
        LifecycleState.FINALIZED,
        LifecycleState.ERROR,
    },
    LifecycleState.ERROR: {
        LifecycleState.INITIALIZING,
        LifecycleState.READY,
        LifecycleState.RUNNING,
        LifecycleState.STOPPING,
        LifecycleState.STOPPED,
        LifecycleState.FINALIZING,
        LifecycleState.FINALIZED,
    },
}
