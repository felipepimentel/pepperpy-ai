"""History tracking functionality.

This module provides functionality for tracking and managing context
history, including state transitions and event logging.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.utils.errors import PepperpyError
from .state import State, StateError


class HistoryError(PepperpyError):
    """History error."""
    pass


@dataclass
class HistoryEntry:
    """History entry data."""
    
    state: State
    event: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar("T")


class HistoryTracker(ABC):
    """Base class for history trackers."""
    
    def __init__(self, name: str, max_entries: Optional[int] = None):
        """Initialize tracker.
        
        Args:
            name: Tracker name
            max_entries: Optional maximum number of entries to keep
        """
        self.name = name
        self.max_entries = max_entries
        self._entries: List[HistoryEntry] = []
        
    @property
    def entries(self) -> List[HistoryEntry]:
        """Get history entries."""
        return self._entries
        
    def add_entry(self, entry: HistoryEntry) -> None:
        """Add history entry.
        
        Args:
            entry: Entry to add
        """
        self._entries.append(entry)
        
        if self.max_entries and len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
            
    def clear_history(self) -> None:
        """Clear history entries."""
        self._entries.clear()
        
    @abstractmethod
    async def record_transition(
        self,
        from_state: Optional[State],
        to_state: State,
        event: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record state transition.
        
        Args:
            from_state: Optional source state
            to_state: Target state
            event: Transition event
            data: Optional transition data
            metadata: Optional transition metadata
            
        Raises:
            HistoryError: If recording fails
        """
        entry = HistoryEntry(
            state=to_state,
            event=event,
            data=data or {},
            metadata=metadata or {},
        )
        self.add_entry(entry)
        
    def validate(self) -> None:
        """Validate tracker state."""
        if not self.name:
            raise ValueError("Tracker name cannot be empty")
            
        if self.max_entries is not None and self.max_entries <= 0:
            raise ValueError("Max entries must be positive")
