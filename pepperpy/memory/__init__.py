"""Memory management module.

This module provides a unified interface for managing different types of memory
storage, including:
- Short-term (Redis)
- Medium-term (vector stores)
- Long-term (PostgreSQL)
"""

from pepperpy.memory.base import (
    BaseMemory,
    BaseMemoryStore,
    MemoryEntry,
    MemoryIndex,
    MemoryManager,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryType,
)
from pepperpy.memory.config import MemoryConfig
from pepperpy.memory.errors import MemoryError, MemoryKeyError, MemoryTypeError
from pepperpy.memory.factory import MemoryStoreType, create_memory_store
from pepperpy.memory.types import MemoryResult

__all__ = [
    "BaseMemory",
    "BaseMemoryStore",
    "MemoryConfig",
    "MemoryEntry",
    "MemoryError",
    "MemoryIndex",
    "MemoryKeyError",
    "MemoryManager",
    "MemoryQuery",
    "MemoryResult",
    "MemoryScope",
    "MemorySearchResult",
    "MemoryStoreType",
    "MemoryType",
    "MemoryTypeError",
    "create_memory_store",
]
