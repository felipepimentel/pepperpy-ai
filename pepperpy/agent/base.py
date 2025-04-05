"""
PepperPy Agent Base Module.

Base interfaces and abstractions for agent functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from pepperpy.agent.task import Message, TaskBase


class AgentProvider(Protocol):
    """Protocol defining agent provider interface."""

    async def initialize(self) -> None:
        """Initialize the agent provider."""
        ...

    async def execute(self, task: str | TaskBase) -> list[Message]:
        """Execute a task using the agent.

        Args:
            task: Task to execute (string or task object)

        Returns:
            List of messages from the execution
        """
        ...

    async def reset(self) -> None:
        """Reset the agent state."""
        ...


class BaseAgentProvider(ABC):
    """Base implementation for agent providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize base agent provider.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent provider.

        Implementations should set self.initialized to True when complete.
        """
        self.initialized = True

    @abstractmethod
    async def execute(self, task: str | TaskBase) -> list[Message]:
        """Execute a task using the agent.

        Args:
            task: Task to execute (string or task object)

        Returns:
            List of messages from the execution
        """
        if not self.initialized:
            await self.initialize()

        # Implementations should handle task execution
        return []

    async def reset(self) -> None:
        """Reset the agent state."""
        # Default implementation - providers can override
        pass
