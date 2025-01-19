"""Base module for handling conversations and chat history."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class MessageRole(Enum):
    """Roles for conversation messages."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "message_id": str(self.message_id),
            "parent_id": str(self.parent_id) if self.parent_id else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary format."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data["metadata"],
            message_id=UUID(data["message_id"]),
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None
        )


@dataclass
class Conversation:
    """Manages a conversation with history and context."""
    
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_id: UUID = field(default_factory=uuid4)
    max_messages: Optional[int] = None
    
    def add_message(
        self,
        content: str,
        role: MessageRole,
        parent_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a new message to the conversation.
        
        Args:
            content: The message content.
            role: Role of the message sender.
            parent_id: Optional ID of parent message.
            metadata: Optional metadata for the message.
            
        Returns:
            The created message.
        """
        message = Message(
            role=role,
            content=content,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # Trim history if needed
        if self.max_messages and len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
            
        return message
    
    def get_context_window(
        self,
        num_messages: Optional[int] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Get recent message history formatted for LLM context.
        
        Args:
            num_messages: Optional number of recent messages to include.
            include_metadata: Whether to include message metadata.
            
        Returns:
            List of formatted messages.
        """
        messages = self.messages[-num_messages:] if num_messages else self.messages
        
        formatted = []
        for msg in messages:
            formatted_msg: Dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content
            }
            if include_metadata:
                formatted_msg["metadata"] = msg.metadata
            formatted.append(formatted_msg)
            
        return formatted
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary format."""
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
            "conversation_id": str(self.conversation_id),
            "max_messages": self.max_messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary format."""
        return cls(
            messages=[Message.from_dict(msg) for msg in data["messages"]],
            metadata=data["metadata"],
            conversation_id=UUID(data["conversation_id"]),
            max_messages=data["max_messages"]
        ) 