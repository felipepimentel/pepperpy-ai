"""Memory implementations for the agents module.

This module provides agent-specific memory implementations using the core
memory management system.
"""

import asyncio
from typing import Any, List, cast

from pepperpy.agents.base import Memory, Message
from pepperpy.core.memory import BaseMemory, MemoryManager


class MessageMemory(BaseMemory):
    """Memory item for storing agent messages.

    This class extends BaseMemory to provide message-specific storage
    and retrieval functionality.
    """

    def __init__(self, message: Message) -> None:
        """Initialize message memory.

        Args:
            message: The message to store
        """
        super().__init__(name=f"message_{message.role}")
        self.message = message
        self.set_metadata("role", message.role)
        self.set("content", message.content)

        # Acesse name com getattr para evitar erro de linter
        name = getattr(message, "name", None)
        if name:
            self.set("name", name)

    def load(self, path: str) -> None:
        """Load memory from storage.

        Args:
            path: Path to load from
        """
        # Messages are ephemeral and not persisted
        pass

    def save(self, path: str) -> None:
        """Save memory to storage.

        Args:
            path: Path to save to
        """
        # Messages are ephemeral and not persisted
        pass


class SimpleMemory(Memory):
    """Simple memory implementation for agents using core memory management.

    This implementation uses the core memory management system to provide
    thread safety, metadata tracking, and access statistics.
    """

    def __init__(self):
        """Initialize the memory."""
        self._manager = MemoryManager()
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "SimpleMemory":
        """Enter async context."""
        await self._manager.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self._manager.__aexit__(exc_type, exc_val, exc_tb)

    async def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: The message to add.
        """
        async with self._lock:
            memory = MessageMemory(message)
            self._manager.add(memory)

    async def get_messages(self) -> List[Message]:
        """Get all messages from memory.

        Returns:
            List of messages.
        """
        async with self._lock:
            memories = self._manager.filter(lambda _: True)
            return [cast(MessageMemory, m).message for m in memories]

    async def get_messages_by_role(self, role: str) -> List[Message]:
        """Get messages from a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of messages from the specified role.
        """
        async with self._lock:
            memories = self._manager.filter(lambda m: m.get_metadata("role") == role)
            return [cast(MessageMemory, m).message for m in memories]

    async def clear(self) -> None:
        """Clear all messages from memory."""
        async with self._lock:
            self._manager.clear_all()
