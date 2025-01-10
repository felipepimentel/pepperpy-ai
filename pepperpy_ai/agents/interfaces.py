"""Agent interface definitions."""

from typing import Any, Protocol, runtime_checkable

from ..ai_types import AIResponse
from .types import AgentConfig


@runtime_checkable
class Agent(Protocol):
    """Agent interface."""

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
