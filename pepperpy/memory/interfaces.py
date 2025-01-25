"""Memory interfaces for Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle


T = TypeVar('T')


class MemoryError(PepperpyError):
    """Memory error class."""
    pass


class BaseMemory(Lifecycle, ABC):
    """Base class for memory implementations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize memory.
        
        Args:
            config: Optional memory configuration.
        """
        super().__init__("memory", config)
        self._is_initialized = False
    
    @abstractmethod
    async def add(self, key: str, value: T) -> None:
        """Add an item to memory.
        
        Args:
            key: Key to store the value under.
            value: Value to store.
            
        Raises:
            MemoryError: If the operation fails.
        """
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get an item from memory.
        
        Args:
            key: Key to retrieve.
            
        Returns:
            The stored value if found, None otherwise.
            
        Raises:
            MemoryError: If the operation fails.
        """
        pass
    
    @abstractmethod
    async def remove(self, key: str) -> None:
        """Remove an item from memory.
        
        Args:
            key: Key to remove.
            
        Raises:
            MemoryError: If the operation fails.
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all items from memory.
        
        Raises:
            MemoryError: If the operation fails.
        """
        pass


class ShortTermMemory(BaseMemory, Generic[T]):
    """Short-term memory implementation.
    
    This memory type is volatile and typically has a limited capacity.
    """
    
    def __init__(
        self,
        capacity: int = 100,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize short-term memory.
        
        Args:
            capacity: Maximum number of items to store.
            config: Optional memory configuration.
        """
        super().__init__(config)
        self._capacity = capacity
        self._memory: Dict[str, T] = {}
    
    async def add(self, key: str, value: T) -> None:
        """Add an item to memory.
        
        If the memory is at capacity, the oldest item will be removed.
        
        Args:
            key: Key to store the value under.
            value: Value to store.
            
        Raises:
            MemoryError: If the operation fails.
        """
        if len(self._memory) >= self._capacity:
            oldest_key = next(iter(self._memory))
            await self.remove(oldest_key)
        self._memory[key] = value
    
    async def get(self, key: str) -> Optional[T]:
        """Get an item from memory.
        
        Args:
            key: Key to retrieve.
            
        Returns:
            The stored value if found, None otherwise.
        """
        return self._memory.get(key)
    
    async def remove(self, key: str) -> None:
        """Remove an item from memory.
        
        Args:
            key: Key to remove.
        """
        self._memory.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all items from memory."""
        self._memory.clear()


class LongTermMemory(BaseMemory, Generic[T]):
    """Long-term memory implementation.
    
    This memory type is persistent and typically has a larger capacity.
    """
    
    def __init__(
        self,
        storage_path: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize long-term memory.
        
        Args:
            storage_path: Path to store memory data.
            config: Optional memory configuration.
        """
        super().__init__(config)
        self._storage_path = storage_path
        self._memory: Dict[str, T] = {}
    
    async def add(self, key: str, value: T) -> None:
        """Add an item to memory.
        
        Args:
            key: Key to store the value under.
            value: Value to store.
            
        Raises:
            MemoryError: If the operation fails.
        """
        self._memory[key] = value
        await self._save()
    
    async def get(self, key: str) -> Optional[T]:
        """Get an item from memory.
        
        Args:
            key: Key to retrieve.
            
        Returns:
            The stored value if found, None otherwise.
            
        Raises:
            MemoryError: If the operation fails.
        """
        await self._load()
        return self._memory.get(key)
    
    async def remove(self, key: str) -> None:
        """Remove an item from memory.
        
        Args:
            key: Key to remove.
            
        Raises:
            MemoryError: If the operation fails.
        """
        self._memory.pop(key, None)
        await self._save()
    
    async def clear(self) -> None:
        """Clear all items from memory.
        
        Raises:
            MemoryError: If the operation fails.
        """
        self._memory.clear()
        await self._save()
    
    async def _save(self) -> None:
        """Save memory to storage.
        
        Raises:
            MemoryError: If the save operation fails.
        """
        try:
            import json
            with open(self._storage_path, 'w') as f:
                json.dump(self._memory, f)
        except Exception as e:
            raise MemoryError(f"Failed to save memory: {e}")
    
    async def _load(self) -> None:
        """Load memory from storage.
        
        Raises:
            MemoryError: If the load operation fails.
        """
        try:
            import json
            with open(self._storage_path, 'r') as f:
                self._memory = json.load(f)
        except FileNotFoundError:
            self._memory = {} 