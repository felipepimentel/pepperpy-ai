"""Memory store module for managing agent memory.

This module provides the base memory store interface and factory function
for creating memory stores. Memory stores are used to persist agent state,
conversation history, and other data needed for agent operation.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Protocol, Type, TypeVar

from pepperpy.core.errors import ConfigurationError


class IMemoryStore(Protocol):
    """Protocol defining the memory store interface."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the memory store."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory store."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up memory store resources."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Any:
        """Get a value from the store."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set a value in the store."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from the store."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the store."""
        pass


T = TypeVar("T", bound=IMemoryStore)

# Registry of memory store types
_memory_store_types: dict[str, Type[IMemoryStore]] = {}


def register_memory_store(store_type: str) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a memory store type.

    Args:
        store_type: Unique identifier for the store type

    Returns:
        Decorator function that registers the store class

    """

    def decorator(cls: Type[T]) -> Type[T]:
        if store_type in _memory_store_types:
            raise ValueError(f"Memory store type already registered: {store_type}")
        _memory_store_types[store_type] = cls  # type: ignore
        return cls

    return decorator


class BaseMemoryStore(ABC):
    """Base class for memory store implementations."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the memory store."""
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory store."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up memory store resources."""
        ...

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the store."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set a value in the store."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from the store."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the store."""
        ...


class MemoryStore(BaseMemoryStore):
    """In-memory store implementation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the memory store.

        Args:
            config: Optional configuration dictionary

        """
        super().__init__(config or {})
        self._store: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the memory store."""
        if self._initialized:
            return
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up memory store resources."""
        if not self._initialized:
            return
        await self.clear()
        self._initialized = False

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the store.

        Args:
            key: Key to get

        Returns:
            The value if found, None otherwise

        """
        return self._store.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set a value in the store.

        Args:
            key: Key to set
            value: Value to store

        """
        self._store[key] = value

    async def delete(self, key: str) -> None:
        """Delete a value from the store.

        Args:
            key: Key to delete

        """
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: Key to check

        Returns:
            True if the key exists, False otherwise

        """
        return key in self._store

    async def clear(self) -> None:
        """Clear all values from the store."""
        self._store.clear()


async def create_memory_store(config: Dict[str, Any]) -> BaseMemoryStore:
    """Create a memory store instance.

    Args:
        config: Store configuration

    Returns:
        BaseMemoryStore: Memory store instance

    Raises:
        ConfigurationError: If store type is unknown

    """
    store_type = config.get("store_type", "memory")
    if store_type != "memory":
        raise ConfigurationError(f"Unknown memory store type: {store_type}")

    return MemoryStore(config)
