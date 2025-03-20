"""Agent Core Module.

This module provides the core agent functionality, including memory management,
intent recognition, and action execution.

Example:
    >>> from pepperpy.agent.internal.agent import Agent
    >>> agent = Agent("assistant")
    >>> agent.add_memory("User likes Python")
    >>> response = agent.process("What language do I like?")
    >>> assert "Python" in response
"""

from typing import Any, Dict, List, Optional, Set

from pepperpy.core.validation import ValidationError

from .intent import Intent
from .memory import Memory


class Agent:
    """AI agent with memory and capabilities.

    This class represents an AI agent with memory management, intent
    recognition, and plugin capabilities. It can process user input,
    maintain context, and execute actions.

    Args:
        name: Agent name
        metadata: Additional agent metadata

    Example:
        >>> agent = Agent("assistant")
        >>> agent.add_memory("User name is Alice")
        >>> response = agent.process("What's my name?")
        >>> assert "Alice" in response
    """

    def __init__(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize agent.

        Args:
            name: Agent name
            metadata: Additional agent metadata

        Raises:
            ValidationError: If name is empty
        """
        if not name:
            raise ValidationError("Agent name cannot be empty")

        self.name = name
        self.metadata = metadata or {}
        self.memories: List[Memory] = []
        self.capabilities: Set[str] = set()

    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
    ) -> None:
        """Add a memory entry.

        Args:
            content: Memory content
            metadata: Additional metadata
            importance: Memory importance (0-1)

        Raises:
            ValidationError: If content is empty or importance is invalid

        Example:
            >>> agent.add_memory(
            ...     "User prefers dark mode",
            ...     metadata={"source": "settings"},
            ...     importance=0.8
            ... )
        """
        if not content:
            raise ValidationError("Memory content cannot be empty")

        memory = Memory(
            content=content,
            metadata=metadata or {},
            importance=importance,
        )
        self.memories.append(memory)

    def get_memories(
        self,
        min_importance: Optional[float] = None,
        max_count: Optional[int] = None,
    ) -> List[Memory]:
        """Get agent memories.

        Args:
            min_importance: Minimum importance threshold (0-1)
            max_count: Maximum number of memories to return

        Returns:
            List of memories sorted by importance

        Example:
            >>> agent.add_memory("Important fact", importance=0.9)
            >>> agent.add_memory("Less important", importance=0.3)
            >>> memories = agent.get_memories(min_importance=0.5)
            >>> assert len(memories) == 1
        """
        memories = sorted(
            self.memories,
            key=lambda m: m.importance,
            reverse=True,
        )

        if min_importance is not None:
            memories = [m for m in memories if m.importance >= min_importance]

        if max_count is not None:
            memories = memories[:max_count]

        return memories

    def recognize_intent(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Intent:
        """Recognize intent from input.

        Args:
            input_text: User input text
            context: Additional context

        Returns:
            Intent: Recognized intent

        Example:
            >>> intent = agent.recognize_intent(
            ...     "What's the weather in London?"
            ... )
            >>> assert intent.name == "get_weather"
        """
        # TODO[v1.0]: Implement intent recognition
        return Intent(
            name="default",
            confidence=1.0,
            parameters={},
        )

    def process(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Process user input and generate response.

        Args:
            input_text: User input text
            context: Additional context

        Returns:
            str: Agent response

        Example:
            >>> response = agent.process(
            ...     "What's my name?",
            ...     context={"session_id": "123"}
            ... )
        """
        # TODO[v1.0]: Implement input processing
        return f"Processing: {input_text}"

    def add_capability(self, capability: str) -> None:
        """Add a capability to the agent.

        Args:
            capability: Capability name

        Example:
            >>> agent.add_capability("weather_lookup")
            >>> assert "weather_lookup" in agent.capabilities
        """
        self.capabilities.add(capability)

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a capability.

        Args:
            capability: Capability name to check

        Returns:
            bool: True if agent has capability

        Example:
            >>> agent.add_capability("math")
            >>> assert agent.has_capability("math")
            >>> assert not agent.has_capability("unknown")
        """
        return capability in self.capabilities

    def get_capabilities(self) -> Set[str]:
        """Get all agent capabilities.

        Returns:
            Set of capability names

        Example:
            >>> agent.add_capability("math")
            >>> agent.add_capability("weather")
            >>> caps = agent.get_capabilities()
            >>> assert "math" in caps
            >>> assert "weather" in caps
        """
        return self.capabilities.copy()

    def clear_memories(
        self,
        min_importance: Optional[float] = None,
    ) -> None:
        """Clear agent memories.

        Args:
            min_importance: Only clear memories below this importance (0-1)

        Example:
            >>> agent.add_memory("Temp data", importance=0.3)
            >>> agent.add_memory("Important", importance=0.9)
            >>> agent.clear_memories(min_importance=0.5)
            >>> memories = agent.get_memories()
            >>> assert len(memories) == 1
            >>> assert memories[0].content == "Important"
        """
        if min_importance is not None:
            self.memories = [m for m in self.memories if m.importance >= min_importance]
        else:
            self.memories.clear()
