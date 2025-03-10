"""Public interfaces for PepperPy Memory module.

This module provides a stable public interface for the memory functionality.
It exposes the core memory abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.memory.core import (
    Document,
    Fact,
    Interaction,
    Memory,
    MemoryFilter,
    MemoryItem,
    MemoryItemType,
    MemoryStorageBase,
    Message,
    create_memory,
)

# Re-export everything
__all__ = [
    # Classes
    "Document",
    "Fact",
    "Interaction",
    "Memory",
    "MemoryFilter",
    "MemoryItem",
    "MemoryItemType",
    "MemoryStorageBase",
    "Message",
    # Functions
    "create_memory",
]
