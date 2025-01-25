"""Conversation data store."""

from collections import deque
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID
from threading import Lock
import copy
from datetime import datetime

from pepperpy.shared.types.message_types import Message, MessageRole
from .. import ContextManager
from ..utils.logger import get_logger
from .state import State, StateManager
from .history import HistoryEntry, HistoryTracker

logger = get_logger(__name__)

class MessageDict(TypedDict):
    """Dictionary representation of a message."""

    role: str
    content: str
    message_id: str
    metadata: Dict[str, Any]
    parent_id: Optional[str]


class Conversation:
    """Manages a conversation with message history."""

    def __init__(self, max_messages: int = 100) -> None:
        """Initialize conversation.

        Args:
            max_messages: Maximum number of messages to keep in history.
        """
        self.max_messages = max_messages
        self.messages: deque[Message] = deque(maxlen=max_messages)

    def add_message(
        self,
        content: str,
        role: MessageRole,
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[UUID] = None
    ) -> Message:
        """Add a message to the conversation.

        Args:
            content: Message content.
            role: Role of the message sender.
            metadata: Optional metadata for the message.
            parent_id: Optional ID of parent message.

        Returns:
            The created message.
        """
        message = Message(
            content=content,
            role=role,
            metadata=metadata or {},
            parent_id=parent_id
        )
        self.messages.append(message)
        return message

    def get_context_window(self, include_metadata: bool = False) -> List[MessageDict]:
        """Get conversation context window.

        Args:
            include_metadata: Whether to include message metadata.

        Returns:
            List of messages in dictionary format.
        """
        messages = []
        for message in self.messages:
            msg_dict: MessageDict = {
                "role": message.role.value,
                "content": message.content,
                "message_id": str(message.message_id),
                "metadata": message.metadata if include_metadata else {},
                "parent_id": str(message.parent_id) if message.parent_id else None
            }
            messages.append(msg_dict)
        return messages

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary format."""
        return {
            "max_messages": self.max_messages,
            "messages": [msg.to_dict() for msg in self.messages]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary format."""
        conv = cls(max_messages=data["max_messages"])
        for msg_data in data["messages"]:
            msg = Message.from_dict(msg_data)
            conv.messages.append(msg)
        return conv

class PepperpyStateManager(StateManager):
    """Concrete implementation of StateManager for Pepperpy context."""
    
    async def transition_to(self, name: str) -> None:
        """Transition to a new state.
        
        Args:
            name: Name of the state to transition to.
        """
        if name not in self._states:
            raise ValueError(f"State {name} does not exist")
        self._current_state = name

class PepperpyHistoryTracker(HistoryTracker):
    """Concrete implementation of HistoryTracker for Pepperpy context."""
    
    async def record_transition(
        self,
        from_state: Optional[State],
        to_state: State,
        event: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a state transition.
        
        Args:
            from_state: Previous state (optional)
            to_state: New state
            event: Event that triggered the transition
            data: Optional data associated with the transition
            metadata: Optional metadata associated with the transition
        """
        entry = HistoryEntry(
            state=to_state,
            event=event,
            data=data or {},
            metadata=metadata or {}
        )
        self.add_entry(entry)

class PepperpyContextManager(ContextManager):
    """Context manager implementation for Pepperpy framework."""
    
    def __init__(self):
        """Initialize the context manager."""
        self._context: Dict[str, Any] = {}
        self._lock = Lock()
        self._state = PepperpyStateManager("pepperpy_context")
        self._history = PepperpyHistoryTracker("pepperpy_context")
        
        # Initialize default state
        default_state = State(
            name="default",
            data={},
            metadata={"created_at": datetime.now().isoformat()}
        )
        self._state.add_state(default_state)
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current context.
        
        Returns:
            Dict containing current context data.
        """
        with self._lock:
            return copy.deepcopy(self._context)
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set the current context.
        
        Args:
            context: New context data to set.
        """
        with self._lock:
            old_context = copy.deepcopy(self._context)
            self._context = copy.deepcopy(context)
            
            # Create new state
            new_state = State(
                name=f"state_{datetime.now().isoformat()}",
                data=self._context,
                metadata={"updated_at": datetime.now().isoformat()}
            )
            self._state.add_state(new_state)
            
            # Record history
            self._history.add_entry(HistoryEntry(
                state=new_state,
                event="set_context",
                data={"old_context": old_context, "new_context": self._context}
            ))
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the current context with new values.
        
        Args:
            updates: Dictionary of updates to apply.
        """
        with self._lock:
            old_context = copy.deepcopy(self._context)
            self._context.update(copy.deepcopy(updates))
            
            # Create new state
            new_state = State(
                name=f"state_{datetime.now().isoformat()}",
                data=self._context,
                metadata={"updated_at": datetime.now().isoformat()}
            )
            self._state.add_state(new_state)
            
            # Record history
            self._history.add_entry(HistoryEntry(
                state=new_state,
                event="update_context",
                data={"old_context": old_context, "new_context": self._context}
            ))
    
    def get_history(self) -> HistoryTracker:
        """Get the context history.
        
        Returns:
            HistoryTracker object containing context changes.
        """
        return self._history
    
    def get_state_manager(self) -> StateManager:
        """Get the state manager.
        
        Returns:
            StateManager object managing context states.
        """
        return self._state
    
    def clear(self) -> None:
        """Clear the current context."""
        with self._lock:
            old_context = copy.deepcopy(self._context)
            self._context = {}
            
            # Create new state
            new_state = State(
                name=f"state_{datetime.now().isoformat()}",
                data={},
                metadata={"cleared_at": datetime.now().isoformat()}
            )
            self._state.add_state(new_state)
            
            # Record history
            self._history.add_entry(HistoryEntry(
                state=new_state,
                event="clear_context",
                data={"old_context": old_context}
            ))
    
    def rollback(self) -> Optional[Dict[str, Any]]:
        """Rollback to the previous context state.
        
        Returns:
            Previous context state if available, None otherwise.
        """
        with self._lock:
            entries = self._history.entries
            if len(entries) > 1:
                previous_entry = entries[-2]  # Get second to last entry
                self._context = copy.deepcopy(previous_entry.state.data)
                return self._context
            return None 