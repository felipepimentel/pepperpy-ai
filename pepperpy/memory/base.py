"""Memory system base interfaces.

This module defines the core interfaces for the memory system, including
the base memory interface and memory entry types.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, Field, validator

from pepperpy.monitoring import logger

K = TypeVar("K", str, UUID)  # Key type
V = TypeVar("V", bound=dict[str, Any])  # Value type
T = TypeVar("T", bound=dict[str, Any])  # Generic type for entries


class MemoryScope(str, Enum):
    """Scope of memory storage."""

    SESSION = "session"  # Persists for session duration
    AGENT = "agent"  # Persists for agent lifetime
    GLOBAL = "global"  # Persists globally


class MemoryType(str, Enum):
    """Types of memory storage."""

    SHORT_TERM = "short_term"  # Volatile, fast access
    MEDIUM_TERM = "medium_term"  # Semi-persistent
    LONG_TERM = "long_term"  # Persistent, indexed


class MemoryIndex(str, Enum):
    """Types of memory indices."""

    SEMANTIC = "semantic"  # Semantic similarity search
    TEMPORAL = "temporal"  # Time-based search
    SPATIAL = "spatial"  # Location-based search
    CAUSAL = "causal"  # Cause-effect relationships
    CONTEXTUAL = "contextual"  # Context-based search


class MemoryQuery(BaseModel):
    """Memory query parameters.

    Attributes:
        query: Search query
        index_type: Type of index to use
        filters: Query filters
        limit: Maximum results
        offset: Result offset
        min_score: Minimum similarity score
        key: Single key to retrieve
        keys: Multiple keys to retrieve
        metadata: Metadata filters
        order_by: Field to order by
        order: Order direction (ASC/DESC)
    """

    query: str = Field(..., min_length=1)
    index_type: MemoryIndex = Field(default=MemoryIndex.SEMANTIC)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1)
    offset: int = Field(default=0, ge=0)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    key: str | None = Field(default=None)
    keys: list[str] | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    order_by: str | None = Field(default=None)
    order: str | None = Field(default=None)

    @validator("query")
    def validate_query(self, v: str) -> str:
        """Validate search query."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    @validator("filters")
    def validate_filters(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure filters are immutable."""
        return dict(v)

    @validator("metadata")
    def validate_metadata(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)

    @validator("order")
    def validate_order(self, v: str | None) -> str | None:
        """Validate order direction."""
        if v is not None and v.upper() not in ["ASC", "DESC"]:
            raise ValueError("Order must be ASC or DESC")
        return v.upper() if v else None


class MemoryEntry(BaseModel, Generic[T]):
    """Memory entry.

    Attributes:
        key: Entry key
        value: Entry value
        type: Memory type
        scope: Memory scope
        created_at: Creation timestamp
        expires_at: Expiration timestamp
        metadata: Additional metadata
    """

    key: str
    value: T
    type: MemoryType = Field(default=MemoryType.SHORT_TERM)
    scope: MemoryScope = Field(default=MemoryScope.SESSION)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("metadata")
    def validate_metadata(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metadata is immutable."""
        return dict(v)


class MemorySearchResult(BaseModel, Generic[T]):
    """Memory search result.

    Attributes:
        entry: Memory entry
        score: Similarity score
        highlights: Search highlights
        metadata: Additional result metadata
    """

    entry: MemoryEntry[T]
    score: float = Field(ge=0.0, le=1.0)
    highlights: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("score")
    def validate_score(self, v: float) -> float:
        """Validate similarity score."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


class BaseMemory(ABC, Generic[K, V]):
    """Base interface for memory implementations."""

    @abstractmethod
    async def store(
        self,
        key: K,
        value: V,
        type: MemoryType = MemoryType.SHORT_TERM,
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        indices: set[MemoryIndex] | None = None,
    ) -> MemoryEntry[V]:
        """Store data in memory.

        Args:
            key: Memory key
            value: Value to store
            type: Type of memory storage
            scope: Storage scope
            metadata: Optional metadata
            expires_at: Optional expiration time
            indices: Optional set of indices to maintain

        Returns:
            Created memory entry

        Raises:
            ValueError: If key is invalid
            TypeError: If value type is not supported
            MemoryError: If storage fails
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        key: K,
        type: MemoryType | None = None,
    ) -> MemoryEntry[V]:
        """Retrieve data from memory.

        Args:
            key: Memory key
            type: Optional memory type filter

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found
            ValueError: If key is invalid
            MemoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[V]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            ValueError: If query is invalid
            MemoryError: If search fails
        """
        pass

    @abstractmethod
    async def similar(
        self,
        key: K,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> AsyncIterator[MemorySearchResult[V]]:
        """Find similar entries.

        Args:
            key: Memory key to find similar entries for
            limit: Maximum number of results
            min_score: Minimum similarity score

        Yields:
            Similar entries ordered by similarity

        Raises:
            KeyError: If key not found
            ValueError: If parameters are invalid
            MemoryError: If similarity search fails
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired memory entries.

        Returns:
            Number of entries cleaned up

        Raises:
            MemoryError: If cleanup fails
        """
        pass


class MemoryMetadata(BaseModel):
    """Metadata for stored memory items."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ttl: int | None = None  # Time-to-live in seconds
    tags: list[str] = Field(default_factory=list)
    source_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class MemoryStorage(Protocol[T]):
    """Protocol for memory storage implementations."""

    async def store(
        self, key: str, value: T, metadata: MemoryMetadata | None = None
    ) -> bool:
        """Store data in memory.

        Args:
            key: Unique identifier for the data
            value: Data to store
            metadata: Optional metadata about the stored data

        Returns:
            bool: True if storage successful
        """
        ...

    async def retrieve(self, key: str) -> tuple[T | None, MemoryMetadata | None]:
        """Retrieve data from memory.

        Args:
            key: Key of data to retrieve

        Returns:
            Tuple[Optional[T], Optional[MemoryMetadata]]: Retrieved data and metadata
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete data from memory.

        Args:
            key: Key of data to delete

        Returns:
            bool: True if deletion successful
        """
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            bool: True if key exists
        """
        ...

    async def clear(self) -> None:
        """Clear all data from memory."""
        ...


@runtime_checkable
class MemoryBackend(Protocol[T]):
    """Protocol for memory backend implementations."""

    async def store(
        self,
        key: str,
        value: T,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Store a value in memory.

        Args:
            key: Key to store value under
            value: Value to store
            metadata: Optional metadata about the stored data

        Returns:
            True if stored successfully
        """
        ...

    async def retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters

        Yields:
            Memory results matching the query
        """
        ...

    async def delete(
        self,
        key: str,
    ) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted successfully
        """
        ...

    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        ...

    async def clear(self) -> None:
        """Clear all data from memory."""
        ...


class BaseMemoryStore(ABC, Generic[T]):
    """Base memory store interface.

    This class defines the interface for memory stores. Memory stores are
    responsible for storing and retrieving memory entries.

    Attributes:
        name: Store name
        is_initialized: Whether store is initialized
    """

    def __init__(self, name: str) -> None:
        """Initialize memory store.

        Args:
            name: Store name
        """
        self.name = name
        self.is_initialized = False

    async def initialize(self) -> None:
        """Initialize memory store.

        This method must be called before using the store.
        """
        if self.is_initialized:
            logger.warning(
                "Memory store already initialized", extra={"store": self.name}
            )
            return

        await self._initialize()
        self.is_initialized = True
        logger.info("Memory store initialized", extra={"store": self.name})

    async def cleanup(self) -> None:
        """Clean up memory store.

        This method must be called when the store is no longer needed.
        """
        if not self.is_initialized:
            logger.warning("Memory store not initialized", extra={"store": self.name})
            return

        await self._cleanup()
        self.is_initialized = False
        logger.info("Memory store cleaned up", extra={"store": self.name})

    async def store(self, entry: MemoryEntry[T]) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryError: If storing fails
            RuntimeError: If store is not initialized
        """
        if not self.is_initialized:
            raise RuntimeError("Memory store not initialized")

        await self._store(entry)
        logger.debug(
            "Memory entry stored", extra={"store": self.name, "key": entry.key}
        )

    @abstractmethod
    def _retrieve(self, query: MemoryQuery) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve memory entries.

        Args:
            query: Memory query.

        Yields:
            Memory search results.

        Raises:
            MemoryError: If retrieval fails.
        """
        raise NotImplementedError

    async def retrieve(
        self, query: MemoryQuery
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve memory entries.

        Args:
            query: Memory query.

        Yields:
            Memory search results.

        Raises:
            MemoryError: If retrieval fails.
            RuntimeError: If store is not initialized.
        """
        if not self.is_initialized:
            raise RuntimeError("Memory store not initialized")

        try:
            async for result in self._retrieve(query):
                yield result
        except Exception as e:
            raise MemoryError(f"Failed to retrieve memory entries: {e}") from e

    async def delete(self, key: str) -> None:
        """Delete a memory entry.

        Args:
            key: Entry key

        Raises:
            MemoryError: If deletion fails
            RuntimeError: If store is not initialized
        """
        if not self.is_initialized:
            raise RuntimeError("Memory store not initialized")

        await self._delete(key)
        logger.debug("Memory entry deleted", extra={"store": self.name, "key": key})

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize memory store.

        This method is called by initialize() and must be implemented by
        subclasses.

        Raises:
            MemoryError: If initialization fails
        """
        raise NotImplementedError

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up memory store.

        This method is called by cleanup() and must be implemented by
        subclasses.

        Raises:
            MemoryError: If cleanup fails
        """
        raise NotImplementedError

    @abstractmethod
    async def _store(self, entry: MemoryEntry[T]) -> None:
        """Store a memory entry.

        This method is called by store() and must be implemented by
        subclasses.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryError: If storing fails
        """
        raise NotImplementedError

    @abstractmethod
    async def _delete(self, key: str) -> None:
        """Delete a memory entry.

        This method is called by delete() and must be implemented by
        subclasses.

        Args:
            key: Entry key

        Raises:
            MemoryError: If deletion fails
        """
        raise NotImplementedError


class MemoryError(Exception):
    """Memory system error."""

    pass


class MemoryInitError(MemoryError):
    """Raised when memory store initialization fails."""

    pass


class MemoryCleanupError(MemoryError):
    """Raised when memory store cleanup fails."""

    pass


class MemoryStoreError(MemoryError):
    """Raised when storing a memory entry fails."""

    pass


class MemoryRetrieveError(MemoryError):
    """Raised when retrieving memory entries fails."""

    pass


class MemoryDeleteError(MemoryError):
    """Raised when deleting a memory entry fails."""

    pass


class MemoryManager:
    """Manager for multiple memory stores."""

    def __init__(self) -> None:
        """Initialize the memory manager."""
        self._stores: dict[str, BaseMemoryStore[Any]] = {}

    async def register_store(self, name: str, store: BaseMemoryStore[Any]) -> None:
        """Register a memory store.

        Args:
            name: Name of the store
            store: Memory store instance
        """
        if name in self._stores:
            raise ValueError(f"Memory store '{name}' already registered")

        await store.initialize()
        self._stores[name] = store
        logger.info("Registered memory store", extra={"store_name": name})

    async def get_store(self, name: str) -> BaseMemoryStore[Any]:
        """Get a memory store by name.

        Args:
            name: Name of the store

        Returns:
            The memory store instance

        Raises:
            KeyError: If store not found
        """
        if name not in self._stores:
            raise KeyError(f"Memory store '{name}' not found")
        return self._stores[name]

    async def cleanup(self) -> None:
        """Clean up all memory stores."""
        for name, store in self._stores.items():
            try:
                await store.cleanup()
                logger.info("Cleaned up memory store", extra={"store_name": name})
            except Exception as e:
                logger.error(
                    "Failed to clean up memory store",
                    extra={"store_name": name, "error": str(e)},
                )
