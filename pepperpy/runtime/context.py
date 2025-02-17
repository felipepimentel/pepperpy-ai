"""@file: context.py
@purpose: Runtime context management for the Pepperpy framework
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import contextvars
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.errors import StateError
from pepperpy.core.types import JSON

T = TypeVar("T")


class ContextState(str, Enum):
    """Possible states of a runtime context."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    CLEANING = "cleaning"
    TERMINATED = "terminated"

    def can_transition_to(self, target: "ContextState") -> bool:
        """Check if a state transition is valid.

        Args:
            target: Target state

        Returns:
            Whether the transition is valid

        """
        transitions = {
            ContextState.CREATED: {ContextState.INITIALIZING},
            ContextState.INITIALIZING: {ContextState.READY, ContextState.ERROR},
            ContextState.READY: {
                ContextState.PROCESSING,
                ContextState.CLEANING,
                ContextState.ERROR,
            },
            ContextState.PROCESSING: {ContextState.READY, ContextState.ERROR},
            ContextState.ERROR: {ContextState.READY, ContextState.CLEANING},
            ContextState.CLEANING: {ContextState.TERMINATED},
            ContextState.TERMINATED: set(),
        }
        return target in transitions[self]


@dataclass
class Context:
    """Runtime context for managing state and metadata."""

    id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None
    state: ContextState = field(default=ContextState.CREATED)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Initialize context after creation."""
        self.validate_state()

    def validate_state(self) -> None:
        """Validate context state."""
        if not isinstance(self.state, ContextState):
            raise StateError(f"Invalid context state: {self.state}")

    def update_state(self, new_state: ContextState) -> None:
        """Update context state.

        Args:
            new_state: New state to transition to

        Raises:
            StateError: If state transition is invalid

        """
        if not self.state.can_transition_to(new_state):
            raise StateError(f"Invalid state transition: {self.state} -> {new_state}")
        self.state = new_state
        self.updated_at = datetime.utcnow()

    def to_json(self) -> JSON:
        """Convert context to JSON format.

        Returns:
            JSON representation of context

        """
        return {
            "id": str(self.id),
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "state": self.state.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_json(cls, data: JSON) -> "Context":
        """Create context from JSON data.

        Args:
            data: JSON data to create context from

        Returns:
            Created context instance

        """
        return cls(
            id=UUID(data["id"]),
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            state=ContextState(data["state"]),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class ContextManager:
    """Manager for runtime contexts."""

    def __init__(self) -> None:
        """Initialize context manager."""
        self._contexts: Dict[UUID, Context] = {}
        self._lock = threading.Lock()
        self._current = contextvars.ContextVar[Optional[UUID]](
            "current_context", default=None
        )

    def create(
        self,
        parent_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Create a new context.

        Args:
            parent_id: Optional parent context ID
            metadata: Optional context metadata

        Returns:
            Created context instance

        """
        context = Context(
            parent_id=parent_id,
            metadata=metadata or {},
        )
        with self._lock:
            self._contexts[context.id] = context
        return context

    def get(self, context_id: UUID) -> Optional[Context]:
        """Get a context by ID.

        Args:
            context_id: Context ID to get

        Returns:
            Context instance if found, None otherwise

        """
        return self._contexts.get(context_id)

    def set_current(self, context_id: Optional[UUID]) -> None:
        """Set the current context.

        Args:
            context_id: Context ID to set as current

        """
        self._current.set(context_id)

    def get_current(self) -> Optional[Context]:
        """Get the current context.

        Returns:
            Current context if set, None otherwise

        """
        context_id = self._current.get()
        if context_id is None:
            return None
        return self.get(context_id)

    def remove(self, context_id: UUID) -> None:
        """Remove a context.

        Args:
            context_id: Context ID to remove

        """
        with self._lock:
            if context_id in self._contexts:
                del self._contexts[context_id]
                if self._current.get() == context_id:
                    self._current.set(None)


# Global context manager instance
_context_manager = ContextManager()


def get_current_context() -> Optional[Context]:
    """Get the current context.

    Returns:
        Current context if set, None otherwise

    """
    return _context_manager.get_current()


def set_current_context(context: Optional[Context]) -> None:
    """Set the current context.

    Args:
        context: Context to set as current

    """
    _context_manager.set_current(context.id if context else None)
