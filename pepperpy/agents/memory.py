"""Memory implementations for the agents module."""

import asyncio
from typing import List, cast

from pepperpy.agents.base import Memory, Message
from pepperpy.core.memory import BaseMemory, MemoryManager


class MessageMemory(BaseMemory):
    """Memory item for storing agent messages."""

    message: Message

    def __init__(self, message: Message) -> None:
        """Initialize message memory.

        Args:
            message: The message to store
        """
        super().__init__(metadata={"role": message.role})
        self.message = message


class SimpleMemory(Memory):
    """Simple memory implementation for agents using core memory management.

    This implementation uses the core memory management system to provide
    thread safety, metadata tracking, and access statistics.
    """

    def __init__(self):
        """Initialize the memory."""
        self._manager = MemoryManager()
        self._lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure memory manager is initialized."""
        if not self._initialized:
            await self._manager.__aenter__()
            self._initialized = True

    async def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: The message to add.
        """
        async with self._lock:
            await self._ensure_initialized()
            memory = MessageMemory(message)
            await self._manager.store(memory)

    async def get_messages(self) -> List[Message]:
        """Get all messages from memory.

        Returns:
            List of messages.
        """
        async with self._lock:
            await self._ensure_initialized()
            memories = await self._manager.get_by_filter(lambda _: True)
            return [cast(MessageMemory, m).message for m in memories]

    async def get_messages_by_role(self, role: str) -> List[Message]:
        """Get messages from a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of messages from the specified role.
        """
        async with self._lock:
            await self._ensure_initialized()
            memories = await self._manager.get_by_filter(
                lambda m: m.metadata["role"] == role
            )
            return [cast(MessageMemory, m).message for m in memories]

    async def clear(self) -> None:
        """Clear all messages from memory."""
        async with self._lock:
            await self._ensure_initialized()
            await self._manager.cleanup()

    async def __del__(self) -> None:
        """Clean up resources when object is deleted."""
        if self._initialized:
            await self._manager.__aexit__(None, None, None)
