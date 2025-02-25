"""State transition definitions for the Pepperpy framework.

This module defines state transitions and validation for lifecycle components.
"""

from dataclasses import dataclass
from typing import Dict, Set

from pepperpy.core.types.states import ComponentState


@dataclass
class StateTransition:
    """State transition definition."""

    from_state: ComponentState
    to_state: ComponentState
    description: str


class StateTransitionManager:
    """Manages state transitions for components."""

    _instance = None

    def __new__(cls) -> "StateTransitionManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the manager."""
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._valid_transitions: Dict[ComponentState, Set[ComponentState]] = {
                ComponentState.UNREGISTERED: {
                    ComponentState.CREATED,
                    ComponentState.ERROR,
                },
                ComponentState.CREATED: {
                    ComponentState.INITIALIZING,
                    ComponentState.ERROR,
                },
                ComponentState.INITIALIZING: {
                    ComponentState.READY,
                    ComponentState.ERROR,
                },
                ComponentState.READY: {
                    ComponentState.RUNNING,
                    ComponentState.CLEANING,
                    ComponentState.ERROR,
                },
                ComponentState.RUNNING: {
                    ComponentState.STOPPED,
                    ComponentState.ERROR,
                },
                ComponentState.STOPPED: {
                    ComponentState.CLEANING,
                    ComponentState.ERROR,
                },
                ComponentState.CLEANING: {
                    ComponentState.CLEANED,
                    ComponentState.ERROR,
                },
                ComponentState.CLEANED: {
                    ComponentState.UNREGISTERED,
                    ComponentState.ERROR,
                },
                ComponentState.ERROR: {
                    ComponentState.CLEANING,
                    ComponentState.UNREGISTERED,
                },
                ComponentState.EXECUTING: {
                    ComponentState.READY,
                    ComponentState.ERROR,
                },
            }

    def is_valid_transition(self, from_state: ComponentState, to_state: ComponentState) -> bool:
        """Check if a state transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            bool: Whether the transition is valid
        """
        return to_state in self._valid_transitions.get(from_state, set())

    def get_valid_transitions(self, state: ComponentState) -> Set[ComponentState]:
        """Get valid transitions from a state.

        Args:
            state: Current state

        Returns:
            Set[ComponentState]: Valid target states
        """
        return self._valid_transitions.get(state, set())


def get_transition_manager() -> StateTransitionManager:
    """Get the global StateTransitionManager instance."""
    return StateTransitionManager()


__all__ = [
    "StateTransition",
    "StateTransitionManager",
    "get_transition_manager",
]
