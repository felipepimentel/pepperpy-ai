"""Agent memory management for PepperPy.

This module provides interfaces and implementations for managing agent memory,
including conversation history, context, and state management.

Example:
    >>> from pepperpy.agents.memory import AgentMemory
    >>> memory = AgentMemory()
    >>> await memory.add("user: What's the weather?")
    >>> history = await memory.get_recent(k=5)
"""

from pepperpy.agents.memory.base import AgentMemory, MemoryProvider

__all__ = [
    "AgentMemory",
    "MemoryProvider",
]
