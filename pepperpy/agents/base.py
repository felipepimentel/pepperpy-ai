"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypeVar

from pepperpy_core import Message, Provider

from .types import AgentConfig, Capability, Tool

T = TypeVar("T", bound="BaseAgent")


class Agent(Protocol):
    """Agent protocol defining the interface for all agents."""

    @property
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        ...

    @property
    def capabilities(self) -> list[Capability]:
        """Get agent capabilities."""
        ...

    @property
    def tools(self) -> list[Tool]:
        """Get agent tools."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        ...

    async def initialize(self) -> None:
        """Initialize agent."""
        ...

    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        ...

    def use(self, provider: Provider) -> T:
        """Configure agent to use specific provider."""
        ...

    async def execute(self, task: str, **kwargs: Any) -> Message:
        """Execute agent task."""
        ...


class BaseAgent(ABC):
    """Base agent implementation."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize agent.

        Args:
            config: Agent configuration.
        """
        self.config = config
        self._provider: Provider | None = None
        self._initialized = False
        self._capabilities: list[Capability] = []
        self._tools: list[Tool] = []

    @property
    def capabilities(self) -> list[Capability]:
        """Get agent capabilities."""
        return self._capabilities

    @property
    def tools(self) -> list[Tool]:
        """Get agent tools."""
        return self._tools

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized

    def use(self, provider: Provider) -> T:
        """Configure agent to use specific provider.

        Args:
            provider: Provider instance to use.

        Returns:
            Self for method chaining.
        """
        self._provider = provider
        return self

    async def initialize(self) -> None:
        """Initialize agent."""
        if not self._provider:
            raise ValueError("Provider not configured. Use .use(provider) first.")
        await self._setup()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        await self._teardown()
        self._initialized = False

    @abstractmethod
    async def _setup(self) -> None:
        """Setup agent resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown agent resources."""
        pass

    @abstractmethod
    async def execute(self, task: str, **kwargs: Any) -> Message:
        """Execute agent task.

        Args:
            task: Task description.
            **kwargs: Additional task parameters.

        Returns:
            Message: Agent response message.
        """
        pass
