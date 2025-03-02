"""Memory module for PepperPy.

This module provides memory capabilities for storing and retrieving data.
"""

# Re-export public interfaces
# Import internal implementations
from pepperpy.memory.base import ContextualMemory, MemoryInterface, VectorMemory
from pepperpy.memory.in_memory import SimpleMemory
from pepperpy.memory.public import (
    ConversationMemory,
    MemoryCapability,
    WorkingMemory,
)

__all__ = [
    # Public interfaces
    "MemoryCapability",
    "ConversationMemory",
    "WorkingMemory",
    # Implementation classes
    "MemoryInterface",
    "ContextualMemory",
    "VectorMemory",
    "SimpleMemory",
]
