"""Conversation memory module."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class MessageRole(Enum):
    """Message role enum."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """Represents a message in a conversation."""
    
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate message after initialization."""
        if not isinstance(self.role, MessageRole):
            raise ValueError("Role must be a MessageRole enum")
        
        if not self.content:
            raise ValueError("Message content cannot be empty")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary.
        
        Returns:
            Dictionary representation of message
        """
        return {
            "id": str(self.id),
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary.
        
        Args:
            data: Dictionary representation of message
            
        Returns:
            Message instance
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        required_fields = {"id", "role", "content"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
        )


@dataclass
class Conversation:
    """Represents a conversation with message history."""
    
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate conversation after initialization."""
        if not isinstance(self.messages, list):
            raise ValueError("Messages must be a list")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
    
    def add_message(self, message: Message) -> None:
        """Add message to conversation.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_messages(
        self,
        role: Optional[MessageRole] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Message]:
        """Get messages from conversation.
        
        Args:
            role: Optional role to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            List of messages matching filters
        """
        messages = self.messages
        
        if role:
            messages = [m for m in messages if m.role == role]
        
        if start_time:
            messages = [m for m in messages if m.timestamp >= start_time]
        
        if end_time:
            messages = [m for m in messages if m.timestamp <= end_time]
        
        return messages
    
    def clear(self) -> None:
        """Clear all messages from conversation."""
        self.messages.clear()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary.
        
        Returns:
            Dictionary representation of conversation
        """
        return {
            "id": str(self.id),
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary.
        
        Args:
            data: Dictionary representation of conversation
            
        Returns:
            Conversation instance
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        required_fields = {"id", "messages"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return cls(
            messages=[Message.from_dict(m) for m in data["messages"]],
            metadata=data.get("metadata", {}),
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
        ) 