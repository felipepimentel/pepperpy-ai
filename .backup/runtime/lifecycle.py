"""@file: lifecycle.py
@purpose: Runtime lifecycle management for the Pepperpy framework
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.errors import StateError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON
from pepperpy.runtime.context import Context, ContextState, get_current_context

logger = get_logger(__name__)

T = TypeVar("T")


class LifecycleState(str, Enum):
    """Possible states in a component's lifecycle."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    RESUMING = "resuming"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"

    def can_transition_to(self, target: "LifecycleState") -> bool:
        """Check if a state transition is valid.

        Args:
            target: Target state

        Returns:
            Whether the transition is valid

        """
        transitions = {
            LifecycleState.CREATED: {LifecycleState.INITIALIZING},
            LifecycleState.INITIALIZING: {LifecycleState.READY, LifecycleState.ERROR},
            LifecycleState.READY: {
                LifecycleState.STARTING,
                LifecycleState.ERROR,
                LifecycleState.TERMINATED,
            },
            LifecycleState.STARTING: {
                LifecycleState.RUNNING,
                LifecycleState.ERROR,
            },
            LifecycleState.RUNNING: {
                LifecycleState.PAUSING,
                LifecycleState.STOPPING,
                LifecycleState.ERROR,
            },
            LifecycleState.PAUSING: {LifecycleState.PAUSED, LifecycleState.ERROR},
            LifecycleState.PAUSED: {
                LifecycleState.RESUMING,
                LifecycleState.STOPPING,
                LifecycleState.ERROR,
            },
            LifecycleState.RESUMING: {LifecycleState.RUNNING, LifecycleState.ERROR},
            LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.ERROR},
            LifecycleState.STOPPED: {
                LifecycleState.STARTING,
                LifecycleState.TERMINATED,
                LifecycleState.ERROR,
            },
            LifecycleState.ERROR: {
                LifecycleState.READY,
                LifecycleState.STOPPED,
                LifecycleState.TERMINATED,
            },
            LifecycleState.TERMINATED: set(),
        }
        return target in transitions[self]


@dataclass
class Lifecycle:
    """Manages the lifecycle of a runtime component."""

    id: UUID = field(default_factory=uuid4)
    state: LifecycleState = field(default=LifecycleState.CREATED)
    context: Optional[Context] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Initialize lifecycle after creation."""
        self.validate_state()

    def validate_state(self) -> None:
        """Validate lifecycle state."""
        if not isinstance(self.state, LifecycleState):
            raise StateError(f"Invalid lifecycle state: {self.state}")

    def update_state(self, new_state: LifecycleState) -> None:
        """Update lifecycle state.

        Args:
            new_state: New state to transition to

        Raises:
            StateError: If state transition is invalid

        """
        if not self.state.can_transition_to(new_state):
            raise StateError(f"Invalid state transition: {self.state} -> {new_state}")
        self.state = new_state
        self.updated_at = datetime.utcnow()

        # Update context state if present
        if self.context:
            try:
                context_state = self._map_to_context_state(new_state)
                self.context.update_state(context_state)
            except Exception as e:
                logger.error(f"Failed to update context state: {e}")

    def _map_to_context_state(self, state: LifecycleState) -> ContextState:
        """Map lifecycle state to context state.

        Args:
            state: Lifecycle state to map

        Returns:
            Corresponding context state

        """
        mapping = {
            LifecycleState.CREATED: ContextState.CREATED,
            LifecycleState.INITIALIZING: ContextState.INITIALIZING,
            LifecycleState.READY: ContextState.READY,
            LifecycleState.STARTING: ContextState.PROCESSING,
            LifecycleState.RUNNING: ContextState.PROCESSING,
            LifecycleState.PAUSING: ContextState.PROCESSING,
            LifecycleState.PAUSED: ContextState.READY,
            LifecycleState.RESUMING: ContextState.PROCESSING,
            LifecycleState.STOPPING: ContextState.CLEANING,
            LifecycleState.STOPPED: ContextState.READY,
            LifecycleState.ERROR: ContextState.ERROR,
            LifecycleState.TERMINATED: ContextState.TERMINATED,
        }
        return mapping[state]

    def to_json(self) -> JSON:
        """Convert lifecycle to JSON format.

        Returns:
            JSON representation of lifecycle

        """
        return {
            "id": str(self.id),
            "state": self.state.value,
            "context_id": str(self.context.id) if self.context else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_json(cls, data: JSON) -> "Lifecycle":
        """Create lifecycle from JSON data.

        Args:
            data: JSON data to create lifecycle from

        Returns:
            Created lifecycle instance

        """
        return cls(
            id=UUID(data["id"]),
            state=LifecycleState(data["state"]),
            context=None,  # Context must be set separately
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class LifecycleManager:
    """Manager for runtime lifecycles."""

    def __init__(self) -> None:
        """Initialize lifecycle manager."""
        self._lifecycles: Dict[UUID, Lifecycle] = {}
        self._lock = threading.Lock()
        self._state_hooks: Dict[LifecycleState, Set[Callable[[UUID], None]]] = {
            state: set() for state in LifecycleState
        }

    def create(
        self,
        context: Optional[Context] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Lifecycle:
        """Create a new lifecycle.

        Args:
            context: Optional context to associate with lifecycle
            metadata: Optional lifecycle metadata

        Returns:
            Created lifecycle instance

        """
        lifecycle = Lifecycle(
            context=context or get_current_context(),
            metadata=metadata or {},
        )
        with self._lock:
            self._lifecycles[lifecycle.id] = lifecycle
        return lifecycle

    def get(self, lifecycle_id: UUID) -> Optional[Lifecycle]:
        """Get a lifecycle by ID.

        Args:
            lifecycle_id: Lifecycle ID to get

        Returns:
            Lifecycle instance if found, None otherwise

        """
        return self._lifecycles.get(lifecycle_id)

    def remove(self, lifecycle_id: UUID) -> None:
        """Remove a lifecycle.

        Args:
            lifecycle_id: Lifecycle ID to remove

        """
        with self._lock:
            if lifecycle_id in self._lifecycles:
                del self._lifecycles[lifecycle_id]

    def add_state_hook(
        self, state: LifecycleState, hook: Callable[[UUID], None]
    ) -> None:
        """Add a state change hook.

        Args:
            state: State to hook into
            hook: Hook function to call

        """
        with self._lock:
            self._state_hooks[state].add(hook)

    def remove_state_hook(
        self, state: LifecycleState, hook: Callable[[UUID], None]
    ) -> None:
        """Remove a state change hook.

        Args:
            state: State to remove hook from
            hook: Hook function to remove

        """
        with self._lock:
            self._state_hooks[state].discard(hook)

    def _trigger_state_hooks(self, lifecycle_id: UUID, state: LifecycleState) -> None:
        """Trigger state change hooks.

        Args:
            lifecycle_id: ID of lifecycle that changed state
            state: New state

        """
        for hook in self._state_hooks[state]:
            try:
                hook(lifecycle_id)
            except Exception as e:
                logger.error(f"State hook failed: {e}")


# Global lifecycle manager instance
_lifecycle_manager = LifecycleManager()


def get_lifecycle_manager() -> LifecycleManager:
    """Get the global lifecycle manager.

    Returns:
        Global lifecycle manager instance

    """
    return _lifecycle_manager
