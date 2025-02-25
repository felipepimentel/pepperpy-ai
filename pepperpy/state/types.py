"""Core types for the state management system.

This module defines the core types used throughout the state management system,
including state enums, metadata classes, and transition types.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class State(Enum):
    """Standard states for components in the system.

    These states represent the possible states a component can be in throughout
    its lifecycle.

    Example:
        >>> state = State.REGISTERED
        >>> assert state.value == "registered"
    """

    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class StateMetadata:
    """Metadata associated with a state.

    Args:
        description (str): Human-readable description of the state.
        timestamp (float): Unix timestamp when the state was entered.
        metadata (Optional[Dict[str, Any]]): Additional metadata key-value pairs.

    Example:
        >>> metadata = StateMetadata(
        ...     description="Component registered successfully",
        ...     timestamp=datetime.now().timestamp(),
        ...     metadata={"registration_id": "123"}
        ... )
    """

    description: str
    timestamp: float
    metadata: dict[str, Any] | None = None


@dataclass
class TransitionHooks:
    """Hooks that can be executed during state transitions.

    Args:
        pre_transition (Optional[callable]): Hook to run before transition.
        post_transition (Optional[callable]): Hook to run after transition.
        on_error (Optional[callable]): Hook to run if transition fails.

    Example:
        >>> def pre_hook(): print("Pre transition")
        >>> def post_hook(): print("Post transition")
        >>> hooks = TransitionHooks(pre_hook, post_hook)
    """

    pre_transition: Callable | None = None
    post_transition: Callable | None = None
    on_error: Callable | None = None


@dataclass
class Transition:
    """Represents a state transition with metadata and hooks.

    Args:
        from_state (State): The starting state.
        to_state (State): The target state.
        hooks (Optional[TransitionHooks]): Hooks to run during transition.
        metadata (Optional[Dict[str, Any]]): Additional transition metadata.

    Example:
        >>> transition = Transition(
        ...     from_state=State.REGISTERED,
        ...     to_state=State.READY,
        ...     hooks=TransitionHooks(),
        ...     metadata={"reason": "initialization complete"}
        ... )
    """

    from_state: State
    to_state: State
    hooks: TransitionHooks | None = None
    metadata: dict[str, Any] | None = None


__all__ = ["State", "StateMetadata", "Transition", "TransitionHooks"]
