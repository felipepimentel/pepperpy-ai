"""Memory store factory module."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pepperpy.core.logging import get_logger
from pepperpy.memory.base import BaseMemoryStore
from pepperpy.memory.errors import MemoryTypeError
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.stores.memory import InMemoryStore

# Configure logger
logger = get_logger(__name__)


class MemoryStoreType(str, Enum):
    """Types of memory stores."""

    MEMORY = "memory"  # In-memory store
    COMPOSITE = "composite"  # Composite store


def create_memory_store(
    store_type: MemoryStoreType,
    config: Optional[Dict[str, Any]] = None,
    stores: Optional[List[BaseMemoryStore[Dict[str, Any]]]] = None,
) -> BaseMemoryStore[Dict[str, Any]]:
    """Create a memory store instance.

    Args:
        store_type: Type of memory store to create
        config: Store configuration
        stores: List of stores for composite store

    Returns:
        Memory store instance

    Raises:
        MemoryTypeError: If store type is invalid

    """
    if store_type == MemoryStoreType.COMPOSITE:
        if not stores:
            stores = []
        return CompositeMemoryStore(name="composite", stores=stores, config=config)
    elif store_type == MemoryStoreType.MEMORY:
        return InMemoryStore(name=str(store_type), config=config)
    else:
        raise MemoryTypeError(f"Invalid memory store type: {store_type}")
