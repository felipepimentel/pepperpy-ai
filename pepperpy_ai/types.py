"""Common type definitions."""

from enum import Enum
from typing import Any

JsonDict = dict[str, Any]


class MessageRole(str, Enum):
    """Message role types."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class AIMessage:
    """AI message type."""

    def __init__(self, role: MessageRole | str, content: str) -> None:
        """Initialize message.

        Args:
            role: Message role
            content: Message content
        """
        self.role = role if isinstance(role, MessageRole) else MessageRole(role)
        self.content = content

    def to_dict(self) -> JsonDict:
        """Convert to dictionary."""
        return {"role": self.role.value, "content": self.content}

    @classmethod
    def from_dict(cls, data: JsonDict) -> "AIMessage":
        """Create from dictionary."""
        return cls(role=data["role"], content=data["content"])
