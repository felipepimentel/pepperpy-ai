"""Storage protocols for Pepperpy data."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, runtime_checkable

# Type variables for storage types
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class StorageBackend(Protocol[T]):
    """Protocol for objects that can be used as storage backends."""
    
    async def get(self, key: str) -> Optional[T]:
        """Get value by key."""
        ...
        
    async def set(self, key: str, value: T) -> None:
        """Set value for key."""
        ...
        
    async def delete(self, key: str) -> None:
        """Delete value by key."""
        ...
        
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...
        
    async def clear(self) -> None:
        """Clear all values."""
        ...

@runtime_checkable
class VectorStore(StorageBackend[T], Protocol[T]):
    """Protocol for objects that can be used as vector stores."""
    
    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to store."""
        ...
        
    async def search_vectors(
        self,
        query_vector: List[float],
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Search for similar vectors."""
        ...
        
    @property
    def dimension(self) -> int:
        """Return vector dimension."""
        ...

@runtime_checkable
class DocumentStore(StorageBackend[T], Protocol[T]):
    """Protocol for objects that can be used as document stores."""
    
    async def add_documents(
        self,
        documents: List[T],
        index: Optional[str] = None
    ) -> List[str]:
        """Add documents to store."""
        ...
        
    async def search_documents(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Search for documents."""
        ...
        
    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get document by ID."""
        ...

@runtime_checkable
class MemoryStore(StorageBackend[T], Protocol[T]):
    """Protocol for objects that can be used as memory stores."""
    
    async def add(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None
    ) -> None:
        """Add value with optional TTL."""
        ...
        
    async def get_with_ttl(
        self,
        key: str
    ) -> Optional[tuple[T, Optional[int]]]:
        """Get value and remaining TTL."""
        ...
        
    async def extend_ttl(
        self,
        key: str,
        ttl: int
    ) -> bool:
        """Extend TTL for key."""
        ...

@runtime_checkable
class Cache(MemoryStore[T], Protocol[T]):
    """Protocol for objects that can be used as caches."""
    
    async def get_or_set(
        self,
        key: str,
        default_factory: Any,
        ttl: Optional[int] = None
    ) -> T:
        """Get value or set default."""
        ...
        
    async def invalidate(
        self,
        pattern: str
    ) -> int:
        """Invalidate keys matching pattern."""
        ...
        
    @property
    def size(self) -> int:
        """Return number of cached items."""
        ... 