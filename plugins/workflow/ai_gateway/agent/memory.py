"""Memory implementations for agents.

This module provides different memory implementations that agents can use
to store and retrieve information during their operation.
"""

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SimpleMemory:
    """Simple in-memory storage for agents."""

    def __init__(self, max_size: int = 100):
        """Initialize memory.

        Args:
            max_size: Maximum number of items to store
        """
        self._data: dict[str, Any] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def add(self, key: str, value: Any) -> None:
        """Add an item to memory.

        Args:
            key: Key to store the value under
            value: Value to store
        """
        async with self._lock:
            if len(self._data) >= self._max_size and key not in self._data:
                # Remove the oldest item if at capacity
                oldest_key = next(iter(self._data))
                del self._data[oldest_key]

            self._data[key] = value

    async def get(self, key: str) -> Any | None:
        """Retrieve an item from memory.

        Args:
            key: Key to retrieve

        Returns:
            Stored value, or None if not found
        """
        return self._data.get(key)

    async def update(self, key: str, value: Any) -> None:
        """Update an item in memory.

        Args:
            key: Key to update
            value: New value
        """
        await self.add(key, value)

    async def remove(self, key: str) -> None:
        """Remove an item from memory.

        Args:
            key: Key to remove
        """
        async with self._lock:
            if key in self._data:
                del self._data[key]

    async def clear(self) -> None:
        """Clear all memory."""
        async with self._lock:
            self._data.clear()


class LRUMemory:
    """Memory with least recently used (LRU) eviction policy."""

    def __init__(self, max_size: int = 100):
        """Initialize memory.

        Args:
            max_size: Maximum number of items to store
        """
        self._data: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def add(self, key: str, value: Any) -> None:
        """Add an item to memory.

        Args:
            key: Key to store the value under
            value: Value to store
        """
        async with self._lock:
            if key in self._data:
                # Move to end if already exists
                self._data.pop(key)
            elif len(self._data) >= self._max_size:
                # Remove the least recently used item if at capacity
                self._data.popitem(last=False)

            self._data[key] = value

    async def get(self, key: str) -> Any | None:
        """Retrieve an item from memory.

        Args:
            key: Key to retrieve

        Returns:
            Stored value, or None if not found
        """
        async with self._lock:
            if key not in self._data:
                return None

            # Move to end (most recently used)
            value = self._data.pop(key)
            self._data[key] = value
            return value

    async def update(self, key: str, value: Any) -> None:
        """Update an item in memory.

        Args:
            key: Key to update
            value: New value
        """
        await self.add(key, value)

    async def remove(self, key: str) -> None:
        """Remove an item from memory.

        Args:
            key: Key to remove
        """
        async with self._lock:
            if key in self._data:
                self._data.pop(key)

    async def clear(self) -> None:
        """Clear all memory."""
        async with self._lock:
            self._data.clear()


class ConversationMemory:
    """Memory for storing conversation history."""

    def __init__(self, max_messages: int = 50):
        """Initialize memory.

        Args:
            max_messages: Maximum number of messages to store
        """
        self._messages: list[dict[str, Any]] = []
        self._max_messages = max_messages
        self._lock = asyncio.Lock()

    async def add_message(
        self, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a message to the conversation.

        Args:
            role: Role of the message sender
            content: Message content
            metadata: Additional metadata
        """
        async with self._lock:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            self._messages.append(message)

            # Trim if necessary
            if len(self._messages) > self._max_messages:
                self._messages = self._messages[-self._max_messages :]

    async def get_history(
        self, limit: int | None = None, roles: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get conversation history.

        Args:
            limit: Maximum number of messages to return
            roles: Only include messages from these roles

        Returns:
            List of messages
        """
        messages = self._messages.copy()

        if roles:
            messages = [m for m in messages if m["role"] in roles]

        if limit:
            messages = messages[-limit:]

        return messages

    async def clear(self) -> None:
        """Clear all messages."""
        async with self._lock:
            self._messages.clear()


class HierarchicalMemory:
    """Hierarchical memory with multiple storage layers."""

    def __init__(self, short_term_size: int = 50, long_term_size: int = 500):
        """Initialize memory.

        Args:
            short_term_size: Maximum short-term memory size
            long_term_size: Maximum long-term memory size
        """
        self._short_term = SimpleMemory(max_size=short_term_size)
        self._long_term = LRUMemory(max_size=long_term_size)
        self._lock = asyncio.Lock()

    async def add(self, key: str, value: Any, long_term: bool = False) -> None:
        """Add an item to memory.

        Args:
            key: Key to store the value under
            value: Value to store
            long_term: Whether to store in long-term memory
        """
        if long_term:
            await self._long_term.add(key, value)
        else:
            await self._short_term.add(key, value)

    async def get(self, key: str) -> Any | None:
        """Retrieve an item from memory.

        Args:
            key: Key to retrieve

        Returns:
            Stored value, or None if not found
        """
        # Check short-term memory first
        value = await self._short_term.get(key)
        if value is not None:
            return value

        # Check long-term memory
        return await self._long_term.get(key)

    async def update(self, key: str, value: Any, long_term: bool = False) -> None:
        """Update an item in memory.

        Args:
            key: Key to update
            value: New value
            long_term: Whether to store in long-term memory
        """
        await self.add(key, value, long_term)

    async def remove(self, key: str) -> None:
        """Remove an item from memory.

        Args:
            key: Key to remove
        """
        await self._short_term.remove(key)
        await self._long_term.remove(key)

    async def clear(self) -> None:
        """Clear all memory."""
        await self._short_term.clear()
        await self._long_term.clear()


def create_memory(memory_type: str = "simple", **config) -> Any:
    """Create a memory instance.

    Args:
        memory_type: Type of memory to create
        **config: Additional configuration

    Returns:
        Memory instance
    """
    if memory_type == "simple":
        max_size = config.get("max_size", 100)
        return SimpleMemory(max_size=max_size)
    elif memory_type == "lru":
        max_size = config.get("max_size", 100)
        return LRUMemory(max_size=max_size)
    elif memory_type == "conversation":
        max_messages = config.get("max_messages", 50)
        return ConversationMemory(max_messages=max_messages)
    elif memory_type == "hierarchical":
        short_term_size = config.get("short_term_size", 50)
        long_term_size = config.get("long_term_size", 500)
        return HierarchicalMemory(
            short_term_size=short_term_size, long_term_size=long_term_size
        )
    else:
        raise ValueError(f"Unknown memory type: {memory_type}")
