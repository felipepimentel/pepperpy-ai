"""Agent memory management for PepperPy.

This module provides interfaces and implementations for managing agent memory,
including conversation history, context, and state management.

Example:
    >>> from pepperpy.agents.memory import Memory
    >>> memory = Memory("User prefers Python")
    >>> print(memory.content)
    User prefers Python
    >>> print(memory.importance)
    0.5
"""

from pepperpy.agents.memory.base import Memory

__all__ = [
    "Memory",
]
