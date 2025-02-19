"""Memory store factory."""

from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.core.memory.errors import MemoryTypeError
from pepperpy.core.memory.stores.base import BaseMemoryStore
from pepperpy.core.memory.stores.composite import CompositeMemoryStore
from pepperpy.core.memory.stores.memory import InMemoryStore

# Configure logging
logger = get_logger(__name__)

T = TypeVar("T", bound=Dict[str, Any])


class MemoryStoreType(str, Enum):
    """Types of memory stores."""

    MEMORY = "memory"  # In-memory store
    COMPOSITE = "composite"  # Composite store


def create_memory_store(
    store_type: MemoryStoreType,
    stores: Optional[List[BaseMemoryStore[T]]] = None,
) -> BaseMemoryStore[T]:
    """Create a memory store instance.

    Args:
        store_type: Type of memory store to create
        stores: Optional list of stores for composite store

    Returns:
        Memory store instance

    Raises:
        MemoryTypeError: If store type is not supported

    """
    if store_type == MemoryStoreType.MEMORY:
        return InMemoryStore()
    elif store_type == MemoryStoreType.COMPOSITE:
        return CompositeMemoryStore(stores=stores)
    else:
        raise MemoryTypeError(
            f"Unsupported memory store type: {store_type}",
            details={"store_type": store_type},
        )
