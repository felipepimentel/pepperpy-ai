"""Agent interfaces and abstractions."""

import abc
import enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ...core.lifecycle import Lifecycle


class AgentState(enum.Enum):
    """Agent state enumeration."""
    
    IDLE = "idle"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"


@runtime_checkable
class Tool(Protocol):
    """Tool interface."""
    
    async def initialize(self) -> None:
        """Initialize tool."""
        ...
        
    async def cleanup(self) -> None:
        """Clean up tool."""
        ...
        
    async def execute(self, input_data: Any) -> Any:
        """Execute tool.
        
        Args:
            input_data: Input data
            
        Returns:
            Execution result
        """
        ...


class Message:
    """Message class."""
    
    def __init__(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize message.
        
        Args:
            content: Message content
            role: Message role (e.g. user, assistant, system)
            metadata: Optional message metadata
        """
        self.content = content
        self.role = role
        self.metadata = metadata or {}
        
    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.role}: {self.content}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Message instance
        """
        return cls(
            content=data["content"],
            role=data["role"],
            metadata=data.get("metadata"),
        )


class AgentMemory(Lifecycle):
    """Agent memory interface."""
    
    async def add_message(self, message: Message) -> None:
        """Add message to memory.
        
        Args:
            message: Message to add
        """
        pass
        
    async def get_messages(
        self,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            limit: Optional message limit
            filters: Optional message filters
            
        Returns:
            List of messages
        """
        return []
        
    async def clear(self) -> None:
        """Clear memory."""
        pass


@runtime_checkable
class AgentObserver(Protocol):
    """Agent observer interface."""
    
    async def initialize(self) -> None:
        """Initialize observer."""
        ...
        
    async def cleanup(self) -> None:
        """Clean up observer."""
        ...
        
    async def on_message(self, message: Message) -> None:
        """Handle message event.
        
        Args:
            message: Message event
        """
        ...
        
    async def on_process_start(self, input_data: Any) -> None:
        """Handle process start event.
        
        Args:
            input_data: Input data
        """
        ...
        
    async def on_process_end(self, result: Any) -> None:
        """Handle process end event.
        
        Args:
            result: Process result
        """
        ...
        
    async def on_error(self, error: Exception) -> None:
        """Handle error event.
        
        Args:
            error: Error event
        """
        ...
