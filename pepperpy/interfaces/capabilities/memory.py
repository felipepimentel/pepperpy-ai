"""
Memory capability interface.

This module provides the public interface for memory capabilities.
"""

from typing import Any, Dict, List, Optional

from pepperpy.capabilities import CapabilityType
from pepperpy.capabilities.base import BaseCapability, CapabilityConfig


class MemoryCapability(BaseCapability):
    """Base class for memory capabilities.

    This class defines the interface that all memory capabilities must implement.
    """

    def __init__(self, config: Optional[CapabilityConfig] = None):
        """Initialize memory capability.

        Args:
            config: Optional configuration for the capability
        """
        super().__init__(CapabilityType.MEMORY, config)

    async def store(self, key: str, value: Any) -> None:
        """Store a value in memory.

        Args:
            key: Key to store the value under
            value: Value to store

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Memory capability must implement store method")

    async def retrieve(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory.

        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Retrieved value or default

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Memory capability must implement retrieve method")

    async def delete(self, key: str) -> bool:
        """Delete a value from memory.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Memory capability must implement delete method")

    async def clear(self) -> None:
        """Clear all values from memory.

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Memory capability must implement clear method")


class ConversationMemory(MemoryCapability):
    """Memory capability for storing conversation history.

    This class provides methods for storing and retrieving conversation
    messages and context.
    """

    async def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the conversation history.

        Args:
            message: Message to add
        """
        pass

    async def get_messages(
        self, limit: Optional[int] = None, reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """Get messages from the conversation history.

        Args:
            limit: Maximum number of messages to retrieve
            reverse: Whether to return messages in reverse order

        Returns:
            List of messages
        """
        pass

    async def get_context(self) -> Dict[str, Any]:
        """Get the conversation context.

        Returns:
            Conversation context
        """
        pass

    async def set_context(self, context: Dict[str, Any]) -> None:
        """Set the conversation context.

        Args:
            context: Conversation context
        """
        pass


class WorkingMemory(MemoryCapability):
    """Memory capability for storing temporary working data.

    This class provides methods for storing and retrieving
    temporary data during task execution.
    """

    async def store_temporary(self, key: str, value: Any, ttl: int) -> None:
        """Store a value with a time-to-live.

        Args:
            key: Key to store the value under
            value: Value to store
            ttl: Time-to-live in seconds
        """
        pass

    async def get_all(self) -> Dict[str, Any]:
        """Get all values in working memory.

        Returns:
            Dictionary of all key-value pairs
        """
        pass


# Export public classes
__all__ = [
    "MemoryCapability",
    "ConversationMemory",
    "WorkingMemory",
]
