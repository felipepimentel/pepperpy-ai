"""
PepperPy Agent Memory Base.

Base interfaces and implementations for agent memory.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

from pepperpy.core.base import PepperpyError


class MemoryError(PepperpyError):
    """Base error for memory operations."""

    pass


T = TypeVar("T")


class MemoryStore(Generic[T], Protocol):
    """Protocol for memory stores."""

    async def initialize(self) -> None:
        """Initialize the memory store."""
        ...

    async def cleanup(self) -> None:
        """Clean up the memory store."""
        ...

    async def add(self, item: T, metadata: dict[str, Any] | None = None) -> None:
        """Add an item to the memory store.

        Args:
            item: Item to add
            metadata: Optional metadata about the item
        """
        ...

    async def get(self, query: str, limit: int = 5) -> list[tuple[T, float]]:
        """Get items from the memory store.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of (item, score) tuples, sorted by relevance
        """
        ...

    async def clear(self) -> None:
        """Clear the memory store."""
        ...


class BaseMemoryStore(Generic[T], ABC):
    """Base implementation for memory stores."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the memory store.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory store."""
        if self.initialized:
            return
        self.initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the memory store."""
        if not self.initialized:
            return
        self.initialized = False

    @abstractmethod
    async def add(self, item: T, metadata: dict[str, Any] | None = None) -> None:
        """Add an item to the memory store.

        Args:
            item: Item to add
            metadata: Optional metadata about the item
        """
        pass

    @abstractmethod
    async def get(self, query: str, limit: int = 5) -> list[tuple[T, float]]:
        """Get items from the memory store.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of (item, score) tuples, sorted by relevance
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the memory store."""
        pass


class InMemoryStore(BaseMemoryStore[T]):
    """Simple in-memory implementation of a memory store."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the in-memory store.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.items: list[tuple[T, dict[str, Any] | None]] = []

    async def initialize(self) -> None:
        """Initialize the in-memory store."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the in-memory store."""
        self.items = []
        await super().cleanup()

    async def add(self, item: T, metadata: dict[str, Any] | None = None) -> None:
        """Add an item to the in-memory store.

        Args:
            item: Item to add
            metadata: Optional metadata about the item
        """
        self.items.append((item, metadata))

    async def get(self, query: str, limit: int = 5) -> list[tuple[T, float]]:
        """Get items from the in-memory store.

        This implementation performs a simple string match on string items.
        For other types, it returns all items with a score of 1.0.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of (item, score) tuples, sorted by relevance
        """
        results = []

        for item, _ in self.items:
            # For string items, do a simple contains match
            if isinstance(item, str):
                if query.lower() in item.lower():
                    # Simple relevance based on number of query terms present
                    score = sum(
                        term.lower() in item.lower() for term in query.split()
                    ) / len(query.split())
                    results.append((item, score))
            else:
                # For non-string items, just return them with a score of 1.0
                results.append((item, 1.0))

        # Sort by score descending and limit results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def clear(self) -> None:
        """Clear the in-memory store."""
        self.items = []


class VectorMemoryStore(BaseMemoryStore[str]):
    """Vector-based memory store for semantic search.

    Uses embeddings for semantic similarity search.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the vector memory store.

        Args:
            config: Optional configuration dictionary with keys:
                - embedding_provider: Name of the embedding provider to use
                - vector_store_type: Type of vector store to use
        """
        super().__init__(config)
        self.embedding_provider = self.config.get("embedding_provider", "default")
        self.vector_store_type = self.config.get("vector_store_type", "in_memory")
        self.embeddings = None
        self.vector_store = None

    async def initialize(self) -> None:
        """Initialize the vector memory store."""
        await super().initialize()

        # Import the embedding provider and vector store
        # This is a placeholder, actual implementation would create
        # the embedding provider and vector store based on configuration

    async def cleanup(self) -> None:
        """Clean up the vector memory store."""
        self.vector_store = None
        self.embeddings = None
        await super().cleanup()

    async def add(self, item: str, metadata: dict[str, Any] | None = None) -> None:
        """Add an item to the vector memory store.

        Args:
            item: String item to add
            metadata: Optional metadata about the item
        """
        # This is a placeholder, actual implementation would:
        # 1. Generate embedding for the item
        # 2. Store item and embedding in vector store
        pass

    async def get(self, query: str, limit: int = 5) -> list[tuple[str, float]]:
        """Get items from the vector memory store based on semantic similarity.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of (item, similarity_score) tuples, sorted by similarity
        """
        # This is a placeholder, actual implementation would:
        # 1. Generate embedding for the query
        # 2. Perform similarity search in vector store
        # 3. Return results with similarity scores
        return []

    async def clear(self) -> None:
        """Clear the vector memory store."""
        # This is a placeholder, actual implementation would
        # clear the vector store
        pass


def create_memory_store(
    store_type: str | None = None, **config: Any
) -> MemoryStore[Any]:
    """Create a memory store.

    Args:
        store_type: Type of memory store to create
        **config: Configuration parameters

    Returns:
        Configured memory store

    Raises:
        MemoryError: If store type is invalid
    """
    store_type = store_type or "in_memory"

    if store_type == "in_memory":
        return InMemoryStore(config)
    elif store_type == "vector":
        return VectorMemoryStore(config)
    else:
        raise MemoryError(f"Invalid memory store type: {store_type}")
