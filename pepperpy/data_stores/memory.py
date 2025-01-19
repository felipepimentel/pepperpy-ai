"""Memory management module."""

from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pepperpy.data_stores.conversation import Conversation
from pepperpy.shared.types.message_types import Message, MessageDict, MessageRole


class MemoryManager:
    """Manager for conversation memory."""

    def __init__(self, max_messages: int = 100) -> None:
        """Initialize memory manager.

        Args:
            max_messages: Maximum number of messages to store.
        """
        self.conversation = Conversation(max_messages=max_messages)

    def add_message(
        self,
        content: str,
        role: MessageRole,
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[UUID] = None,
    ) -> Message:
        """Add a message to the conversation.

        Args:
            content: Message content.
            role: Message role.
            metadata: Optional message metadata.
            parent_id: Optional parent message ID.

        Returns:
            Added message.
        """
        return self.conversation.add_message(
            content=content,
            role=role,
            metadata=metadata or {},
            parent_id=parent_id,
        )

    def get_context_window(self, include_metadata: bool = False) -> Sequence[MessageDict]:
        """Get conversation context window.

        Args:
            include_metadata: Whether to include message metadata.

        Returns:
            List of messages in context window.
        """
        return self.conversation.get_context_window(include_metadata=include_metadata)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation.clear_history()

    def to_dict(self) -> dict[str, Any]:
        """Convert memory to dictionary format.

        Returns:
            Dictionary representation of memory.
        """
        return self.conversation.to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryManager":
        """Create memory manager from dictionary.

        Args:
            data: Dictionary representation of memory.

        Returns:
            Memory manager instance.
        """
        manager = cls()
        manager.conversation = Conversation.from_dict(data)
        return manager 