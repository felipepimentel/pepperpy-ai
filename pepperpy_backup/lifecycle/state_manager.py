"""Component state management functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError


class StateError(PepperpyError):
    """State error."""
    pass


class StateManager(ABC):
    """Base class for component state managers."""
    
    def __init__(self, name: str):
        """Initialize state manager.
        
        Args:
            name: State manager name
        """
        self.name = name
        self._current_state = None
        self._valid_states: Set[str] = set()
        self._valid_transitions: Dict[str, Set[str]] = {}
        
    @property
    def current_state(self) -> Optional[str]:
        """Get current state."""
        return self._current_state
        
    @property
    def valid_states(self) -> Set[str]:
        """Get valid states."""
        return self._valid_states
        
    def add_state(self, state: str) -> None:
        """Add valid state.
        
        Args:
            state: State to add
        """
        self._valid_states.add(state)
        
    def add_transition(self, from_state: str, to_state: str) -> None:
        """Add valid state transition.
        
        Args:
            from_state: Source state
            to_state: Target state
        """
        if from_state not in self._valid_transitions:
            self._valid_transitions[from_state] = set()
        self._valid_transitions[from_state].add(to_state)
        
    @abstractmethod
    async def transition_to(self, state: str, **kwargs: Any) -> None:
        """Transition to new state.
        
        Args:
            state: Target state
            **kwargs: State-specific transition arguments
            
        Raises:
            StateError: If transition is invalid or fails
        """
        if state not in self._valid_states:
            raise StateError(f"Invalid state: {state}")
            
        if (
            self._current_state is not None
            and state not in self._valid_transitions.get(self._current_state, set())
        ):
            raise StateError(
                f"Invalid transition from {self._current_state} to {state}"
            )
            
        self._current_state = state
        
    def validate(self) -> None:
        """Validate state manager state."""
        if not self.name:
            raise ValueError("State manager name cannot be empty")
            
        if not self._valid_states:
            raise ValueError("No valid states defined") 