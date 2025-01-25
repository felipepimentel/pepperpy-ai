"""State management functionality.

This module provides functionality for managing state in the context
system, including state transitions and validation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from pepperpy.core.utils.errors import PepperpyError


class StateError(PepperpyError):
    """State error."""
    pass


@dataclass
class State:
    """State data."""
    
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent: Optional[str] = None
    children: Set[str] = field(default_factory=set)


class StateManager(ABC):
    """Base class for state managers."""
    
    def __init__(self, name: str):
        """Initialize manager.
        
        Args:
            name: Manager name
        """
        self.name = name
        self._states: Dict[str, State] = {}
        self._current_state: Optional[str] = None
        
    @property
    def current_state(self) -> Optional[State]:
        """Get current state."""
        if self._current_state is None:
            return None
        return self._states.get(self._current_state)
        
    def add_state(self, state: State) -> None:
        """Add state.
        
        Args:
            state: State to add
            
        Raises:
            StateError: If state already exists
        """
        if state.name in self._states:
            raise StateError(f"State already exists: {state.name}")
            
        self._states[state.name] = state
        
        if state.parent:
            parent = self._states.get(state.parent)
            if parent:
                parent.children.add(state.name)
        
    def remove_state(self, name: str) -> None:
        """Remove state.
        
        Args:
            name: State name
            
        Raises:
            StateError: If state not found or has children
        """
        if name not in self._states:
            raise StateError(f"State not found: {name}")
            
        state = self._states[name]
        if state.children:
            raise StateError(f"State has children: {name}")
            
        if state.parent:
            parent = self._states.get(state.parent)
            if parent:
                parent.children.remove(name)
                
        del self._states[name]
        
    @abstractmethod
    async def transition_to(self, name: str) -> None:
        """Transition to state.
        
        Args:
            name: State name
            
        Raises:
            StateError: If state not found or transition invalid
        """
        if name not in self._states:
            raise StateError(f"State not found: {name}")
            
        self._current_state = name
        
    def validate(self) -> None:
        """Validate manager state."""
        if not self.name:
            raise ValueError("Manager name cannot be empty")
            
        # Validate state hierarchy
        for name, state in self._states.items():
            if state.parent and state.parent not in self._states:
                raise StateError(
                    f"Parent state not found for {name}: {state.parent}"
                )
