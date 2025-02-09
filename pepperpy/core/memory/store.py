"""Memory store module for managing agent memory.

This module provides the base memory store interface and factory function
for creating memory stores. Memory stores are used to persist agent state,
conversation history, and other data needed for agent operation.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Protocol, Type, TypeVar

from pepperpy.core.errors import ValidationError


class MemoryStore(Protocol):
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


T = TypeVar("T", bound=MemoryStore)

# Registry of memory store types
_memory_store_types: dict[str, Type[MemoryStore]] = {}


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


async def create_memory_store(config: dict[str, Any]) -> MemoryStore:
    """Create a memory store instance."""
    if "type" not in config:
        raise ValidationError(
            "Missing required field: type",
            details={"field": "type"},
        )

    store_type = config["type"]
    if store_type not in _memory_store_types:
        raise ValidationError(
            f"Unknown memory store type: {store_type}",
            details={"type": store_type},
        )

    store_class = _memory_store_types[store_type]
    return store_class(config)
