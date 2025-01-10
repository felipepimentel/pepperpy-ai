"""Base agent implementation."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from ..ai_types import AIResponse
from .types import AgentConfig


class Agent(Protocol):
    """Agent protocol."""

    @property
    def config(self) -> AgentConfig:
        """Get agent configuration."""
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

    async def execute(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute agent task."""
        ...


class BaseAgent(ABC):
    """Base agent implementation."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize agent."""
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize agent."""
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
    async def execute(self, task: str, **kwargs: Any) -> AIResponse:
        """Execute agent task."""
        pass
