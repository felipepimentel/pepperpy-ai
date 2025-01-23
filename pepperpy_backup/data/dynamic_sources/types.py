"""Type definitions for Pepperpy data module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, runtime_checkable

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


@runtime_checkable
class Embeddable(Protocol):
    """Protocol for objects that can be embedded."""
    
    @abstractmethod
    def to_embedding(self) -> List[float]:
        """Convert object to embedding vector."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return embedding dimension."""
        raise NotImplementedError


@runtime_checkable
class Chunkable(Protocol[T]):
    """Protocol for objects that can be chunked."""
    
    @abstractmethod
    def chunk(
        self,
        chunk_size: int,
        overlap: int = 0
    ) -> List[T]:
        """Split object into chunks.
        
        Args:
            chunk_size: Maximum size of each chunk
            overlap: Number of overlapping items between chunks
            
        Returns:
            List of chunks
        """
        raise NotImplementedError


@runtime_checkable
class SimilarityComparable(Protocol):
    """Protocol for objects that can be compared by similarity."""
    
    @abstractmethod
    def similarity(self, other: Any) -> float:
        """Calculate similarity with another object.
        
        Args:
            other: Object to compare with
            
        Returns:
            Similarity score between 0 and 1
        """
        raise NotImplementedError


@runtime_checkable
class Storable(Protocol):
    """Protocol for objects that can be stored."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Return object ID."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return object metadata."""
        raise NotImplementedError


@runtime_checkable
class Indexable(Storable, Protocol):
    """Protocol for objects that can be indexed."""
    
    @property
    @abstractmethod
    def index_key(self) -> str:
        """Return index key."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def index_value(self) -> Any:
        """Return index value."""
        raise NotImplementedError


@runtime_checkable
class Cacheable(Protocol):
    """Protocol for objects that can be cached."""
    
    @property
    @abstractmethod
    def cache_key(self) -> str:
        """Return cache key."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def ttl(self) -> Optional[int]:
        """Return time-to-live in seconds."""
        raise NotImplementedError


@runtime_checkable
class StorageBackend(Protocol[T]):
    """Protocol for objects that can be used as storage backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get value by key."""
        raise NotImplementedError
        
    @abstractmethod
    async def set(self, key: str, value: T) -> None:
        """Set value for key."""
        raise NotImplementedError
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value by key."""
        raise NotImplementedError
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        raise NotImplementedError
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values."""
        raise NotImplementedError


@runtime_checkable
class VectorStore(StorageBackend[T], Protocol[T]):
    """Protocol for objects that can be used as vector stores."""
    
    @abstractmethod
    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to store.
        
        Args:
            vectors: List of vectors to add
            metadata: Optional metadata for each vector
            
        Returns:
            List of vector IDs
        """
        raise NotImplementedError
        
    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of similar vectors
        """
        raise NotImplementedError
        
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return vector dimension."""
        raise NotImplementedError


@runtime_checkable
class DocumentStore(StorageBackend[T], Protocol[T]):
    """Protocol for objects that can be used as document stores."""
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[T],
        index: Optional[str] = None
    ) -> List[str]:
        """Add documents to store.
        
        Args:
            documents: List of documents to add
            index: Optional index name
            
        Returns:
            List of document IDs
        """
        raise NotImplementedError
        
    @abstractmethod
    async def search_documents(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Search for documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of matching documents
        """
        raise NotImplementedError
        
    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        raise NotImplementedError


@runtime_checkable
class MemoryStore(StorageBackend[T], Protocol[T]):
    """Protocol for objects that can be used as memory stores."""
    
    @abstractmethod
    async def add(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None
    ) -> None:
        """Add value with optional TTL.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Optional time-to-live in seconds
        """
        raise NotImplementedError
        
    @abstractmethod
    async def get_with_ttl(
        self,
        key: str
    ) -> Optional[tuple[T, Optional[int]]]:
        """Get value and remaining TTL.
        
        Args:
            key: Storage key
            
        Returns:
            Tuple of value and remaining TTL if found, None otherwise
        """
        raise NotImplementedError
        
    @abstractmethod
    async def extend_ttl(
        self,
        key: str,
        ttl: int
    ) -> bool:
        """Extend TTL for key.
        
        Args:
            key: Storage key
            ttl: New time-to-live in seconds
            
        Returns:
            True if TTL was extended, False if key not found
        """
        raise NotImplementedError


@runtime_checkable
class Cache(MemoryStore[T], Protocol[T]):
    """Protocol for objects that can be used as caches."""
    
    @abstractmethod
    async def get_or_set(
        self,
        key: str,
        default_factory: Any,
        ttl: Optional[int] = None
    ) -> T:
        """Get value or set default.
        
        Args:
            key: Cache key
            default_factory: Factory function to create default value
            ttl: Optional time-to-live in seconds
            
        Returns:
            Cached value or newly created default
        """
        raise NotImplementedError
        
    @abstractmethod
    async def invalidate(
        self,
        pattern: str
    ) -> int:
        """Invalidate keys matching pattern.
        
        Args:
            pattern: Pattern to match keys against
            
        Returns:
            Number of invalidated keys
        """
        raise NotImplementedError
        
    @property
    @abstractmethod
    def size(self) -> int:
        """Return number of cached items."""
        raise NotImplementedError 