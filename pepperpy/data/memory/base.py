"""Base memory store classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import StorageError, MemoryExpiredError, MemoryCapacityError
from ...core.lifecycle import Lifecycle

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
        self._expires_at = self._created_at + timedelta(seconds=ttl) if ttl else None
        
    @property
    def id(self) -> str:
        """Return memory ID."""
        return self._id
        
    @property
    def content(self) -> Any:
        """Return memory content."""
        return self._content
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return memory metadata."""
        return self._metadata
        
    @property
    def created_at(self) -> datetime:
        """Return memory creation time."""
        return self._created_at
        
    @property
    def expires_at(self) -> Optional[datetime]:
        """Return memory expiration time."""
        return self._expires_at
        
    @property
    def expired(self) -> bool:
        """Return whether memory has expired."""
        if self._expires_at is None:
            return False
            
        return datetime.utcnow() > self._expires_at
        
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.id}, "
            f"content={str(self.content)[:50]}..., "
            f"expires_at={self.expires_at}"
            f")"
        )
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Create memory from dictionary.
        
        Args:
            data: Dictionary with memory data
            
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
            Dictionary with memory data
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "ttl": int((self._expires_at - self._created_at).total_seconds()) if self._expires_at else None,
        }
        
    def validate(self) -> None:
        """Validate memory state."""
        if not self.id:
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
        super().__init__(name)
        self._max_size = max_size
        self._default_ttl = default_ttl
        
    @property
    def max_size(self) -> Optional[int]:
        """Return maximum store size."""
        return self._max_size
        
    @property
    def default_ttl(self) -> Optional[int]:
        """Return default time-to-live."""
        return self._default_ttl
        
    async def add(self, memories: List[Memory]) -> None:
        """Add memories to store.
        
        Args:
            memories: Memories to add
            
        Raises:
            StorageError: If store is not initialized
            MemoryCapacityError: If store is full
        """
        if not self._initialized:
            raise StorageError("Memory store not initialized")
            
        if self._max_size is not None:
            current_size = await self.count()
            if current_size + len(memories) > self._max_size:
                raise MemoryCapacityError(
                    f"Store capacity exceeded: {current_size + len(memories)} > {self._max_size}"
                )
                
        await self._add(memories)
        
    @abstractmethod
    async def _add(self, memories: List[Memory]) -> None:
        """Add memories implementation."""
        pass
        
    async def get(self, id: str) -> Optional[Memory]:
        """Get memory by ID.
        
        Args:
            id: Memory ID
            
        Returns:
            Memory if found and not expired, None otherwise
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Memory store not initialized")
            
        memory = await self._get(id)
        
        if memory is not None and memory.expired:
            await self.delete([id])
            return None
            
        return memory
        
    @abstractmethod
    async def _get(self, id: str) -> Optional[Memory]:
        """Get memory implementation."""
        pass
        
    async def search(
        self,
        query: Any,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Search for memories.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 10)
            filters: Optional metadata filters
            
        Returns:
            List of matching memories
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Memory store not initialized")
            
        memories = await self._search(query, limit, filters)
        
        # Filter expired memories
        valid_memories = []
        expired_ids = []
        
        for memory in memories:
            if memory.expired:
                expired_ids.append(memory.id)
            else:
                valid_memories.append(memory)
                
        if expired_ids:
            await self.delete(expired_ids)
            
        return valid_memories
        
    @abstractmethod
    async def _search(
        self,
        query: Any,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Search implementation."""
        pass
        
    async def delete(self, ids: List[str]) -> None:
        """Delete memories from store.
        
        Args:
            ids: Memory IDs to delete
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Memory store not initialized")
            
        await self._delete(ids)
        
    @abstractmethod
    async def _delete(self, ids: List[str]) -> None:
        """Delete implementation."""
        pass
        
    async def clear(self) -> None:
        """Clear all memories from store.
        
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Memory store not initialized")
            
        await self._clear()
        
    @abstractmethod
    async def _clear(self) -> None:
        """Clear implementation."""
        pass
        
    async def count(self) -> int:
        """Return number of memories in store.
        
        Returns:
            Number of memories
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Memory store not initialized")
            
        return await self._count()
        
    @abstractmethod
    async def _count(self) -> int:
        """Count implementation."""
        pass
        
    def validate(self) -> None:
        """Validate store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Store name cannot be empty")
            
        if self._max_size is not None and self._max_size <= 0:
            raise ValueError("Maximum store size must be positive")
            
        if self._default_ttl is not None and self._default_ttl <= 0:
            raise ValueError("Default TTL must be positive") 