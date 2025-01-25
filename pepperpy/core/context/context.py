"""Context module for managing state and history.

This module provides the Context class that combines state management
and history tracking functionality.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from pepperpy.core.utils.errors import PepperpyError
from .state import State, StateManager
from .history import HistoryEntry, HistoryTracker


class ContextError(PepperpyError):
    """Context error."""
    pass


@dataclass
class Context:
    """Context class for managing state and history.
    
    This class combines state management and history tracking functionality
    to provide a complete context for operations.
    """
    
    name: str
    state_manager: StateManager
    history_tracker: HistoryTracker
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate context after initialization."""
        if not self.name:
            raise ContextError("Context name cannot be empty")
        if not isinstance(self.metadata, dict):
            raise ContextError("Metadata must be a dictionary")
    
    @property
    def current_state(self) -> Optional[State]:
        """Get current state."""
        return self.state_manager.current_state
    
    @property
    def history(self) -> List[HistoryEntry]:
        """Get history entries."""
        return self.history_tracker.entries
    
    async def transition_to(self, state: str) -> None:
        """Transition to state.
        
        Args:
            state: State name
            
        Raises:
            ContextError: If transition fails
        """
        try:
            current = self.current_state
            await self.state_manager.transition_to(state)
            new_state = self.state_manager.current_state
            if new_state:
                await self.history_tracker.record_transition(
                    from_state=current,
                    to_state=new_state,
                    event="state_transition",
                    data={"from": current.name if current else None, "to": state},
                    metadata={"context": self.name}
                )
        except Exception as e:
            raise ContextError(f"Failed to transition to state {state}: {e}")
    
    def add_state(self, state: State) -> None:
        """Add state.
        
        Args:
            state: State to add
            
        Raises:
            ContextError: If adding state fails
        """
        try:
            self.state_manager.add_state(state)
            self.history_tracker.add_entry(
                HistoryEntry(
                    state=state,
                    event="state_added",
                    data={"state": state.name},
                    metadata={"context": self.name}
                )
            )
        except Exception as e:
            raise ContextError(f"Failed to add state {state.name}: {e}")
    
    def remove_state(self, name: str) -> None:
        """Remove state.
        
        Args:
            name: State name
            
        Raises:
            ContextError: If removing state fails
        """
        try:
            state = self.state_manager.current_state
            if state and state.name == name:
                state_to_remove = state
            else:
                state_to_remove = State(name=name)
            
            self.state_manager.remove_state(name)
            self.history_tracker.add_entry(
                HistoryEntry(
                    state=state_to_remove,
                    event="state_removed",
                    data={"state": name},
                    metadata={"context": self.name}
                )
            )
        except Exception as e:
            raise ContextError(f"Failed to remove state {name}: {e}")
    
    def validate(self) -> None:
        """Validate context."""
        try:
            self.state_manager.validate()
            self.history_tracker.validate()
        except Exception as e:
            raise ContextError(f"Context validation failed: {e}") 