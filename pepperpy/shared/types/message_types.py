"""Message type definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TypedDict
from uuid import UUID, uuid4


class MessageDict(TypedDict):
    """Dictionary representation of a message."""

    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    message_id: str
    parent_id: Optional[str]


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

    def to_dict(self) -> MessageDict:
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
    def from_dict(cls, data: MessageDict) -> "Message":
        """Create message from dictionary format."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data["metadata"],
            message_id=UUID(data["message_id"]),
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None
        ) 