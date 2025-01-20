"""Base memory store classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from pepperpy.common.types import PepperpyObject, DictInitializable, Validatable
from pepperpy.common.errors import StorageError, MemoryExpiredError, MemoryCapacityError
from pepperpy.core.lifecycle import Lifecycle


T = TypeVar("T")


class Memory(PepperpyObject, DictInitializable, Validatable):
    """Base class for memories."""
    
    def __init__(
        self,
        id: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Initialize memory.
        
        Args:
            id: Memory ID
            content: Memory content
            metadata: Optional memory metadata
            ttl: Optional time-to-live in seconds
        """
        self._id = id
        self._content = content
        self._metadata = metadata or {}
        self._created_at = datetime.utcnow()
        self._expires_at = (
            self._created_at + timedelta(seconds=ttl)
            if ttl is not None
            else None
        )
        
    @property
    def id(self) -> str:
        """Get memory ID."""
        return self._id
        
    @property
    def content(self) -> Any:
        """Get memory content."""
        return self._content
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get memory metadata."""
        return self._metadata
        
    @property
    def created_at(self) -> datetime:
        """Get memory creation time."""
        return self._created_at
        
    @property
    def expires_at(self) -> Optional[datetime]:
        """Get memory expiration time."""
        return self._expires_at
        
    @property
    def expired(self) -> bool:
        """Check if memory has expired."""
        if self._expires_at is None:
            return False
        return datetime.utcnow() > self._expires_at
        
    def __repr__(self) -> str:
        """Get string representation."""
        return (
            f"Memory(id={self._id}, "
            f"content={self._content}, "
            f"metadata={self._metadata}, "
            f"created_at={self._created_at}, "
            f"expires_at={self._expires_at})"
        )
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Create memory from dictionary.
        
        Args:
            data: Dictionary containing memory data
            
        Returns:
            Memory instance
        """
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata"),
            ttl=data.get("ttl"),
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary.
        
        Returns:
            Dictionary containing memory data
        """
        return {
            "id": self._id,
            "content": self._content,
            "metadata": self._metadata,
            "created_at": self._created_at.isoformat(),
            "expires_at": self._expires_at.isoformat() if self._expires_at else None,
        }
        
    def validate(self) -> None:
        """Validate memory state."""
        if not self._id:
            raise ValueError("Memory ID cannot be empty")


class MemoryStore(Lifecycle, ABC):
    """Base class for memory stores."""
    
    def __init__(
        self,
        name: str,
        max_size: Optional[int] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        """Initialize memory store.
        
        Args:
            name: Store name
            max_size: Optional maximum number of memories
            default_ttl: Optional default time-to-live in seconds
        """
        super().__init__()
        self.name = name
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        
    @property
    def max_size(self) -> Optional[int]:
        """Get maximum store size."""
        return self._max_size
        
    @property
    def default_ttl(self) -> Optional[int]:
        """Get default time-to-live."""
        return self._default_ttl
        
    async def add(self, memories: List[Memory]) -> None:
        """Add memories to store.
        
        Args:
            memories: List of memories to add
            
        Raises:
            MemoryCapacityError: If store is full
            StorageError: If storage operation fails
        """
        if not memories:
            return
            
        async with self._lock:
            # Check capacity
            if self._max_size is not None:
                current_size = await self.count()
                if current_size + len(memories) > self._max_size:
                    raise MemoryCapacityError(
                        message=f"Cannot add {len(memories)} memories, store capacity is {self._max_size}",
                        store_type=self.__class__.__name__,
                        max_size=self._max_size,
                        current_size=current_size,
                    )
                    
            # Add memories
            await self._add(memories)
            
    @abstractmethod
    async def _add(self, memories: List[Memory]) -> None:
        """Add memories to store (implementation).
        
        Args:
            memories: List of memories to add
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
        
    async def get(self, id: str) -> Optional[Memory]:
        """Get memory by ID.
        
        Args:
            id: Memory ID
            
        Returns:
            Memory if found and not expired, None otherwise
            
        Raises:
            StorageError: If storage operation fails
        """
        memory = await self._get(id)
        
        if memory is None:
            return None
            
        if memory.expired:
            await self.delete([id])
            return None
            
        return memory
        
    @abstractmethod
    async def _get(self, id: str) -> Optional[Memory]:
        """Get memory by ID (implementation).
        
        Args:
            id: Memory ID
            
        Returns:
            Memory if found, None otherwise
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
        
    async def search(
        self,
        query: Any,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Search memories.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional search filters
            
        Returns:
            List of matching memories
            
        Raises:
            StorageError: If storage operation fails
        """
        async with self._lock:
            # Get all matching memories
            memories = await self._search(query, limit, filters)
            
            # Filter expired memories
            valid_memories = []
            expired_ids = []
            
            for memory in memories:
                if memory.expired:
                    expired_ids.append(memory.id)
                else:
                    valid_memories.append(memory)
                    
            # Delete expired memories
            if expired_ids:
                await self.delete(expired_ids)
                
            return valid_memories[:limit]
            
    @abstractmethod
    async def _search(
        self,
        query: Any,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Search memories (implementation).
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional search filters
            
        Returns:
            List of matching memories
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
        
    async def delete(self, ids: List[str]) -> None:
        """Delete memories.
        
        Args:
            ids: List of memory IDs to delete
            
        Raises:
            StorageError: If storage operation fails
        """
        if not ids:
            return
            
        async with self._lock:
            await self._delete(ids)
            
    @abstractmethod
    async def _delete(self, ids: List[str]) -> None:
        """Delete memories (implementation).
        
        Args:
            ids: List of memory IDs to delete
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
        
    async def clear(self) -> None:
        """Clear all memories.
        
        Raises:
            StorageError: If storage operation fails
        """
        async with self._lock:
            await self._clear()
            
    @abstractmethod
    async def _clear(self) -> None:
        """Clear all memories (implementation).
        
        Raises:
            StorageError: If storage operation fails
        """
        pass
        
    async def count(self) -> int:
        """Get number of memories.
        
        Returns:
            Number of memories in store
            
        Raises:
            StorageError: If storage operation fails
        """
        async with self._lock:
            count = await self._count()
            return count
            
    @abstractmethod
    async def _count(self) -> int:
        """Get number of memories (implementation).
        
        Returns:
            Number of memories in store
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
        
    def validate(self) -> None:
        """Validate store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Store name cannot be empty") 