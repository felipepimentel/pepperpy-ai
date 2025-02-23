"""Base agent module for the Pepperpy framework.

This module provides the core agent functionality and interfaces that all agents must implement.
It defines the base agent class, agent states, configuration, and common utilities.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from pepperpy.core.base import (
    ComponentBase,
    ComponentCallback,
    ComponentConfig,
    ComponentState,
)
from pepperpy.core.types import AgentID


@dataclass
class AgentConfig(ComponentConfig):
    """Agent configuration."""

    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    capabilities: List[str] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    workflow: Optional[List[Dict[str, Any]]] = None


class AgentCallback(ComponentCallback, Protocol):
    """Protocol for agent callbacks."""

    async def on_state_change(self, agent_id: str, state: ComponentState) -> None:
        """Called when agent state changes."""
        ...

    async def on_error(self, agent_id: str, error: Exception) -> None:
        """Called when agent encounters an error."""
        ...

    async def on_progress(self, agent_id: str, progress: float) -> None:
        """Called when agent makes progress."""
        ...


class BaseAgent(ComponentBase):
    """Base class for all agents.

    This class extends ComponentBase with agent-specific functionality:
    - Model configuration
    - Capabilities management
    - Memory management
    - Workflow integration
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        callback: Optional[AgentCallback] = None,
    ) -> None:
        """Initialize agent.

        Args:
            config: Optional agent configuration
            callback: Optional callback for agent events
        """
        super().__init__(config or AgentConfig(name=self.__class__.__name__), callback)
        self.id = AgentID(self.id)  # Convert ComponentID to AgentID

    @property
    def capabilities(self) -> List[str]:
        """Get agent capabilities."""
        if isinstance(self.config, AgentConfig):
            return self.config.capabilities
        return []

    @property
    def memory(self) -> Dict[str, Any]:
        """Get agent memory."""
        if isinstance(self.config, AgentConfig):
            return self.config.memory
        return {}

    async def _initialize(self) -> None:
        """Initialize agent implementation.

        This method should be implemented by subclasses to perform
        agent-specific initialization.
        """
        pass

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute agent implementation.

        This method should be implemented by subclasses to perform
        agent-specific execution.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result
        """
        pass

    async def _cleanup(self) -> None:
        """Clean up agent implementation.

        This method should be implemented by subclasses to perform
        agent-specific cleanup.
        """
        pass
