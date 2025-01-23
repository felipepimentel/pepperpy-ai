"""Complex state management functionality.

This module provides functionality for managing complex state hierarchies
and transitions, including validation and history tracking.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .history import HistoryTracker
from .state import State, StateError, StateManager


class ComplexStateError(PepperpyError):
    """Complex state error."""
    pass


class ComplexStateManager(StateManager, Lifecycle):
    """Complex state manager implementation."""
    
    def __init__(
        self,
        name: str,
        history_tracker: Optional[HistoryTracker] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize manager.
        
        Args:
            name: Manager name
            history_tracker: Optional history tracker
            config: Optional configuration
        """
        super().__init__(name)
        self._history = history_tracker
        self._config = config or {}
        self._valid_transitions: Dict[str, Set[str]] = {}
        
    def add_valid_transition(self, from_state: str, to_state: str) -> None:
        """Add valid state transition.
        
        Args:
            from_state: Source state name
            to_state: Target state name
            
        Raises:
            ComplexStateError: If states not found
        """
        if from_state not in self._states:
            raise ComplexStateError(f"Source state not found: {from_state}")
            
        if to_state not in self._states:
            raise ComplexStateError(f"Target state not found: {to_state}")
            
        if from_state not in self._valid_transitions:
            self._valid_transitions[from_state] = set()
            
        self._valid_transitions[from_state].add(to_state)
        
    def is_valid_transition(self, from_state: str, to_state: str) -> bool:
        """Check if state transition is valid.
        
        Args:
            from_state: Source state name
            to_state: Target state name
            
        Returns:
            True if transition is valid, False otherwise
        """
        return (
            from_state in self._valid_transitions
            and to_state in self._valid_transitions[from_state]
        )
        
    async def transition_to(self, name: str) -> None:
        """Transition to state.
        
        Args:
            name: Target state name
            
        Raises:
            ComplexStateError: If transition invalid
        """
        if name not in self._states:
            raise ComplexStateError(f"State not found: {name}")
            
        if self._current_state:
            if not self.is_valid_transition(self._current_state, name):
                raise ComplexStateError(
                    f"Invalid transition from {self._current_state} to {name}"
                )
                
        old_state = self.current_state
        self._current_state = name
        
        if self._history:
            await self._history.record_transition(
                from_state=old_state,
                to_state=self._states[name],
                event=f"transition_to_{name}",
            )
            
    async def _initialize(self) -> None:
        """Initialize manager."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up manager."""
        pass
        
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        # Validate transitions
        for from_state, to_states in self._valid_transitions.items():
            if from_state not in self._states:
                raise ComplexStateError(
                    f"Invalid transition source state: {from_state}"
                )
                
            for to_state in to_states:
                if to_state not in self._states:
                    raise ComplexStateError(
                        f"Invalid transition target state: {to_state}"
                    )
