"""Agent Memory Module.

This module provides memory management capabilities for agents,
including memory storage, retrieval, and importance scoring.

Example:
    >>> from pepperpy.agent.internal.memory import Memory
    >>> memory = Memory(
    ...     content="User prefers Python",
    ...     metadata={"source": "conversation"}
    ... )
    >>> assert memory.importance == 0.5
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from pepperpy.core.validation import ValidationError


@dataclass
class Memory:
    """Agent memory entry.

    This class represents a single memory entry in an agent's memory store.
    Each memory has content, creation timestamp, metadata, and an importance
    score that determines its relevance and retention.

    Args:
        content: Memory content
        timestamp: When memory was created
        metadata: Additional memory metadata
        importance: Memory importance score (0-1)

    Example:
        >>> memory = Memory(
        ...     content="User prefers Python",
        ...     metadata={"source": "conversation"}
        ... )
        >>> print(memory.content)
        User prefers Python
        >>> print(memory.importance)
        0.5
    """

    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5

    def __post_init__(self):
        """Validate memory after initialization.

        Raises:
            ValidationError: If importance is not between 0 and 1
        """
        if not 0 <= self.importance <= 1:
            raise ValidationError(
                "Importance must be between 0 and 1",
                field="importance",
                rule="range",
            )

    def update_importance(self, new_importance: float) -> None:
        """Update memory importance score.

        Args:
            new_importance: New importance score (0-1)

        Raises:
            ValidationError: If new_importance is not between 0 and 1

        Example:
            >>> memory = Memory("User likes Python")
            >>> memory.update_importance(0.8)
            >>> assert memory.importance == 0.8
        """
        if not 0 <= new_importance <= 1:
            raise ValidationError(
                "Importance must be between 0 and 1",
                field="importance",
                rule="range",
            )
        self.importance = new_importance

    def merge(self, other: "Memory") -> "Memory":
        """Merge this memory with another memory.

        This method creates a new memory that combines the content and
        metadata of both memories, using the maximum importance score.

        Args:
            other: Memory to merge with

        Returns:
            New merged memory

        Example:
            >>> mem1 = Memory("User likes Python", importance=0.5)
            >>> mem2 = Memory("User codes in Python", importance=0.8)
            >>> merged = mem1.merge(mem2)
            >>> assert merged.importance == 0.8
        """
        return Memory(
            content=f"{self.content}\n{other.content}",
            metadata={**self.metadata, **other.metadata},
            importance=max(self.importance, other.importance),
        )
