"""Memory management module.

This module provides a unified interface for managing different types of memory
storage, including:
- Short-term (Redis)
- Medium-term (vector stores)
- Long-term (PostgreSQL)
"""

from pepperpy.memory.base import BaseMemoryStore, MemoryManager
from pepperpy.memory.config import MemoryConfig
from pepperpy.memory.types import MemoryEntry, MemoryQuery, MemoryResult

__all__ = [
    "BaseMemoryStore",
    "MemoryConfig",
    "MemoryEntry",
    "MemoryManager",
    "MemoryQuery",
    "MemoryResult",
]
