"""
Types and enums for the lifecycle management system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LifecycleState(str, Enum):
    """States in the lifecycle of a component."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FINALIZING = "finalizing"
    FINALIZED = "finalized"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value


@dataclass
class StateTransition:
    """Represents a transition between lifecycle states."""

    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Exception | None = None

    def is_valid(self) -> bool:
        """Check if the transition is valid according to the state machine rules."""
        valid_transitions = {
            LifecycleState.UNINITIALIZED: [
                LifecycleState.INITIALIZING,
                LifecycleState.ERROR,
            ],
            LifecycleState.INITIALIZING: [
                LifecycleState.INITIALIZED,
                LifecycleState.ERROR,
            ],
            LifecycleState.INITIALIZED: [
                LifecycleState.STARTING,
                LifecycleState.FINALIZING,
                LifecycleState.ERROR,
            ],
            LifecycleState.STARTING: [LifecycleState.RUNNING, LifecycleState.ERROR],
            LifecycleState.RUNNING: [LifecycleState.STOPPING, LifecycleState.ERROR],
            LifecycleState.STOPPING: [LifecycleState.STOPPED, LifecycleState.ERROR],
            LifecycleState.STOPPED: [
                LifecycleState.STARTING,
                LifecycleState.FINALIZING,
                LifecycleState.ERROR,
            ],
            LifecycleState.FINALIZING: [LifecycleState.FINALIZED, LifecycleState.ERROR],
            LifecycleState.FINALIZED: [LifecycleState.INITIALIZING],
            LifecycleState.ERROR: [
                LifecycleState.INITIALIZING,
                LifecycleState.FINALIZING,
            ],
        }
        return self.to_state in valid_transitions.get(self.from_state, [])
