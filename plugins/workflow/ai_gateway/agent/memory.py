"""Memory implementations for the agent system.

This module provides various memory implementations for storing and
retrieving agent state and context.
"""

import asyncio
import collections
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")
Key = str
Value = Any


class BaseMemory(ABC):
    """Base class for all memory implementations."""

    def __init__(self, max_size: int = 1000):
        """Initialize memory.
        
        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self._lock = asyncio.Lock()

    @abstractmethod
    async def add(self, key: Key, value: Value) -> None:
        """Add an item to memory.
        
        Args:
            key: Item key
            value: Item value
        """
        pass

    @abstractmethod
    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory.
        
        Args:
            key: Item key
            
        Returns:
            Item value or None if not found
        """
        pass

    @abstractmethod
    async def update(self, key: Key, value: Value) -> None:
        """Update an item in memory.
        
        Args:
            key: Item key
            value: New item value
        """
        pass

    @abstractmethod
    async def remove(self, key: Key) -> None:
        """Remove an item from memory.
        
        Args:
            key: Item key
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all items from memory."""
        pass

    @abstractmethod
    async def get_all(self) -> Dict[Key, Value]:
        """Get all items in memory.
        
        Returns:
            Dictionary of all items
        """
        pass


class SimpleMemory(BaseMemory):
    """Simple memory implementation using a dictionary."""

    def __init__(self, max_size: int = 1000):
        """Initialize simple memory.
        
        Args:
            max_size: Maximum number of items to store
        """
        super().__init__(max_size)
        self._data: Dict[Key, Value] = {}

    async def add(self, key: Key, value: Value) -> None:
        """Add an item to memory.
        
        Args:
            key: Item key
            value: Item value
        """
        async with self._lock:
            if len(self._data) >= self.max_size and key not in self._data:
                # If we're at capacity, we need to remove an item
                # In SimpleMemory, we just remove a random item
                if self._data:
                    del self._data[next(iter(self._data))]
            
            self._data[key] = value

    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory.
        
        Args:
            key: Item key
            
        Returns:
            Item value or None if not found
        """
        return self._data.get(key)

    async def update(self, key: Key, value: Value) -> None:
        """Update an item in memory.
        
        Args:
            key: Item key
            value: New item value
        """
        async with self._lock:
            if key in self._data:
                self._data[key] = value

    async def remove(self, key: Key) -> None:
        """Remove an item from memory.
        
        Args:
            key: Item key
        """
        async with self._lock:
            if key in self._data:
                del self._data[key]

    async def clear(self) -> None:
        """Clear all items from memory."""
        async with self._lock:
            self._data.clear()

    async def get_all(self) -> Dict[Key, Value]:
        """Get all items in memory.
        
        Returns:
            Dictionary of all items
        """
        return self._data.copy()


class LRUMemory(BaseMemory):
    """Memory implementation with least recently used (LRU) eviction policy."""

    def __init__(self, max_size: int = 1000):
        """Initialize LRU memory.
        
        Args:
            max_size: Maximum number of items to store
        """
        super().__init__(max_size)
        self._data: Dict[Key, Value] = {}
        self._lru: collections.OrderedDict = collections.OrderedDict()

    async def add(self, key: Key, value: Value) -> None:
        """Add an item to memory.
        
        Args:
            key: Item key
            value: Item value
        """
        async with self._lock:
            # If key already exists, update it
            if key in self._data:
                self._data[key] = value
                # Move to the end (most recently used)
                self._lru.move_to_end(key)
                return

            # If we're at capacity, remove the least recently used item
            if len(self._data) >= self.max_size:
                # Get the first key (least recently used)
                lru_key, _ = next(iter(self._lru.items()))
                # Remove from data and LRU
                del self._data[lru_key]
                del self._lru[lru_key]

            # Add new item
            self._data[key] = value
            self._lru[key] = None

    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory.
        
        Args:
            key: Item key
            
        Returns:
            Item value or None if not found
        """
        if key not in self._data:
            return None

        # Update LRU order
        async with self._lock:
            self._lru.move_to_end(key)

        return self._data[key]

    async def update(self, key: Key, value: Value) -> None:
        """Update an item in memory.
        
        Args:
            key: Item key
            value: New item value
        """
        if key not in self._data:
            return

        async with self._lock:
            self._data[key] = value
            self._lru.move_to_end(key)

    async def remove(self, key: Key) -> None:
        """Remove an item from memory.
        
        Args:
            key: Item key
        """
        if key not in self._data:
            return

        async with self._lock:
            del self._data[key]
            del self._lru[key]

    async def clear(self) -> None:
        """Clear all items from memory."""
        async with self._lock:
            self._data.clear()
            self._lru.clear()

    async def get_all(self) -> Dict[Key, Value]:
        """Get all items in memory.
        
        Returns:
            Dictionary of all items
        """
        return self._data.copy()


class MemoryItem(Generic[T]):
    """Item stored in memory with metadata."""

    def __init__(self, value: T, metadata: Optional[Dict[str, Any]] = None):
        """Initialize memory item.
        
        Args:
            value: Item value
            metadata: Item metadata
        """
        self.value = value
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.accessed_at = self.created_at
        self.access_count = 0

    def access(self) -> None:
        """Mark item as accessed."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class ConversationMemory(BaseMemory):
    """Memory implementation for storing conversation history."""

    def __init__(self, max_size: int = 100):
        """Initialize conversation memory.
        
        Args:
            max_size: Maximum number of messages to store
        """
        super().__init__(max_size)
        self._messages: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}

    async def add(self, key: Key, value: Dict[str, Any]) -> None:
        """Add a message to conversation history.
        
        Args:
            key: Message ID (not used in this implementation)
            value: Message data
        """
        async with self._lock:
            # Add timestamp if not present
            if "timestamp" not in value:
                value["timestamp"] = datetime.now().isoformat()

            # If we're at capacity, remove oldest message
            if len(self._messages) >= self.max_size:
                self._messages.pop(0)

            self._messages.append(value)

    async def get(self, key: Key) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID.
        
        Args:
            key: Message ID
            
        Returns:
            Message data or None if not found
        """
        # Linear search for message with matching ID
        for message in self._messages:
            if message.get("id") == key:
                return message
        return None

    async def update(self, key: Key, value: Dict[str, Any]) -> None:
        """Update a message in the conversation.
        
        Args:
            key: Message ID
            value: New message data
        """
        async with self._lock:
            for i, message in enumerate(self._messages):
                if message.get("id") == key:
                    self._messages[i] = value
                    break

    async def remove(self, key: Key) -> None:
        """Remove a message from the conversation.
        
        Args:
            key: Message ID
        """
        async with self._lock:
            self._messages = [m for m in self._messages if m.get("id") != key]

    async def clear(self) -> None:
        """Clear all messages from memory."""
        async with self._lock:
            self._messages.clear()
            self._metadata.clear()

    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all messages in conversation.
        
        Returns:
            List of all messages
        """
        return self._messages.copy()

    async def get_metadata(self) -> Dict[str, Any]:
        """Get conversation metadata.
        
        Returns:
            Conversation metadata
        """
        return self._metadata.copy()

    async def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set conversation metadata.
        
        Args:
            metadata: Conversation metadata
        """
        async with self._lock:
            self._metadata.update(metadata)

    async def get_last_n_messages(self, n: int) -> List[Dict[str, Any]]:
        """Get the last N messages.
        
        Args:
            n: Number of messages to retrieve
            
        Returns:
            List of the last N messages
        """
        return self._messages[-n:] if n > 0 else []


class HierarchicalMemory(BaseMemory):
    """Hierarchical memory with multiple tiers.
    
    This memory implementation uses multiple tiers with different
    retention policies:
    - Short-term memory: Fast access, limited size
    - Long-term memory: Larger capacity, slower access
    - Permanent memory: Important information that should be retained
    """

    def __init__(
        self,
        short_term_size: int = 100,
        long_term_size: int = 1000,
        permanent_size: int = 100,
    ):
        """Initialize hierarchical memory.
        
        Args:
            short_term_size: Maximum size for short-term memory
            long_term_size: Maximum size for long-term memory
            permanent_size: Maximum size for permanent memory
        """
        super().__init__(short_term_size + long_term_size + permanent_size)
        self._short_term = LRUMemory(short_term_size)
        self._long_term = LRUMemory(long_term_size)
        self._permanent = SimpleMemory(permanent_size)
        
        # Importance threshold for moving items to long-term memory
        self.importance_threshold = 0.5
        
        # Access count threshold for moving items to long-term memory
        self.access_count_threshold = 3

    async def add(
        self, key: Key, value: Value, importance: float = 0.0, permanent: bool = False
    ) -> None:
        """Add an item to memory.
        
        Args:
            key: Item key
            value: Item value
            importance: Item importance (0.0-1.0)
            permanent: Whether to store in permanent memory
        """
        item = MemoryItem(value, {"importance": importance})
        
        if permanent:
            # Add to permanent memory
            await self._permanent.add(key, item)
        elif importance >= self.importance_threshold:
            # Important items go to long-term memory
            await self._long_term.add(key, item)
        else:
            # Regular items go to short-term memory
            await self._short_term.add(key, item)

    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory.
        
        Args:
            key: Item key
            
        Returns:
            Item value or None if not found
        """
        # Check permanent memory first
        item = await self._permanent.get(key)
        if item is not None:
            item.access()
            return item.value
            
        # Then check short-term memory
        item = await self._short_term.get(key)
        if item is not None:
            item.access()
            
            # If accessed frequently, move to long-term memory
            if item.access_count >= self.access_count_threshold:
                await self._short_term.remove(key)
                await self._long_term.add(key, item)
                
            return item.value
            
        # Finally check long-term memory
        item = await self._long_term.get(key)
        if item is not None:
            item.access()
            return item.value
            
        return None

    async def update(
        self, key: Key, value: Value, importance: Optional[float] = None, permanent: Optional[bool] = None
    ) -> None:
        """Update an item in memory.
        
        Args:
            key: Item key
            value: New item value
            importance: New importance value (if None, keep existing)
            permanent: Whether to move to permanent memory
        """
        # Check where the item currently is
        item = await self._permanent.get(key)
        memory_type = "permanent" if item is not None else None
        
        if item is None:
            item = await self._short_term.get(key)
            memory_type = "short_term" if item is not None else None
            
        if item is None:
            item = await self._long_term.get(key)
            memory_type = "long_term" if item is not None else None
            
        if item is None:
            # Item doesn't exist, just add it
            await self.add(key, value, importance or 0.0, permanent or False)
            return
            
        # Update the item
        item.value = value
        
        if importance is not None:
            item.metadata["importance"] = importance
            
        # Handle memory type changes
        if permanent:
            # Move to permanent memory if requested
            if memory_type != "permanent":
                await self._remove_from_current(key, memory_type)
                await self._permanent.add(key, item)
        elif importance is not None:
            if importance >= self.importance_threshold and memory_type == "short_term":
                # Move from short-term to long-term if importance increased
                await self._short_term.remove(key)
                await self._long_term.add(key, item)
            elif importance < self.importance_threshold and memory_type == "long_term":
                # Move from long-term to short-term if importance decreased
                await self._long_term.remove(key)
                await self._short_term.add(key, item)
        else:
            # Just update in place
            if memory_type == "permanent":
                await self._permanent.update(key, item)
            elif memory_type == "short_term":
                await self._short_term.update(key, item)
            elif memory_type == "long_term":
                await self._long_term.update(key, item)

    async def remove(self, key: Key) -> None:
        """Remove an item from memory.
        
        Args:
            key: Item key
        """
        await self._permanent.remove(key)
        await self._short_term.remove(key)
        await self._long_term.remove(key)

    async def clear(self) -> None:
        """Clear all items from memory."""
        await self._permanent.clear()
        await self._short_term.clear()
        await self._long_term.clear()

    async def get_all(self) -> Dict[Key, Value]:
        """Get all items in memory.
        
        Returns:
            Dictionary of all items
        """
        result = {}
        
        # Get items from all memory tiers
        permanent_items = await self._permanent.get_all()
        short_term_items = await self._short_term.get_all()
        long_term_items = await self._long_term.get_all()
        
        # Extract values from MemoryItems
        for key, item in permanent_items.items():
            result[key] = item.value
            
        for key, item in short_term_items.items():
            result[key] = item.value
            
        for key, item in long_term_items.items():
            result[key] = item.value
            
        return result
        
    async def _remove_from_current(self, key: Key, memory_type: Optional[str]) -> None:
        """Remove an item from its current memory tier.
        
        Args:
            key: Item key
            memory_type: Current memory tier
        """
        if memory_type == "permanent":
            await self._permanent.remove(key)
        elif memory_type == "short_term":
            await self._short_term.remove(key)
        elif memory_type == "long_term":
            await self._long_term.remove(key)


# Factory function to create memory instances
def create_memory(memory_type: str = "simple", **kwargs) -> BaseMemory:
    """Create a memory instance.
    
    Args:
        memory_type: Type of memory to create
        **kwargs: Additional parameters for the memory
        
    Returns:
        Memory instance
        
    Raises:
        ValueError: If memory type is unknown
    """
    if memory_type == "simple":
        return SimpleMemory(**kwargs)
    elif memory_type == "lru":
        return LRUMemory(**kwargs)
    elif memory_type == "conversation":
        return ConversationMemory(**kwargs)
    elif memory_type == "hierarchical":
        return HierarchicalMemory(**kwargs)
    else:
        raise ValueError(f"Unknown memory type: {memory_type}")
