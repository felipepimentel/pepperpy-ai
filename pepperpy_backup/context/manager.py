"""Conversation data store."""

from collections import deque
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID

from pepperpy.shared.types.message_types import Message, MessageRole


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