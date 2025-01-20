"""Protocols for data types in Pepperpy."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, runtime_checkable

# Type variables for protocols
T = TypeVar("T")

@runtime_checkable
class Embeddable(Protocol):
    """Protocol for objects that can be embedded."""
    
    def to_embedding(self) -> List[float]:
        """Convert object to embedding vector."""
        ...
        
    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension."""
        ...

@runtime_checkable
class Chunkable(Protocol[T]):
    """Protocol for objects that can be chunked."""
    
    def chunk(
        self,
        chunk_size: int,
        overlap: int = 0
    ) -> List[T]:
        """Split object into chunks."""
        ...

@runtime_checkable
class SimilarityComparable(Protocol):
    """Protocol for objects that can be compared for similarity."""
    
    def similarity(self, other: Any) -> float:
        """Calculate similarity score with another object."""
        ...

@runtime_checkable
class Storable(Protocol):
    """Protocol for objects that can be stored."""
    
    @property
    def id(self) -> str:
        """Return object ID."""
        ...
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return object metadata."""
        ...

@runtime_checkable
class Indexable(Storable, Protocol):
    """Protocol for objects that can be indexed."""
    
    @property
    def index_key(self) -> str:
        """Return index key."""
        ...
        
    @property
    def index_value(self) -> Any:
        """Return index value."""
        ...

@runtime_checkable
class Cacheable(Protocol):
    """Protocol for objects that can be cached."""
    
    @property
    def cache_key(self) -> str:
        """Return cache key."""
        ...
        
    @property
    def ttl(self) -> Optional[int]:
        """Return time-to-live in seconds."""
        ... 