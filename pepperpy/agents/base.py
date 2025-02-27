"""Interfaces base para o módulo de agentes

Define as interfaces e classes base para os diferentes tipos de agentes
e suas capacidades no framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from pepperpy.core.types.base import BaseComponent
from pepperpy.core.types.enums import AgentID, AgentState


class AgentCapability(Protocol):
    """Protocol for agent capabilities."""

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the capability.

        Args:
            **kwargs: Capability parameters

        Returns:
            Capability result
        """
        ...


class BaseAgent(BaseComponent, ABC):
    """Base class for all agents."""

    def __init__(self, id: UUID, name: str) -> None:
        """Initialize agent.

        Args:
            id: Agent ID
            name: Agent name
        """
        super().__init__(name=name, id=id)
        self._state = AgentState.UNKNOWN
        self._capabilities: Dict[str, AgentCapability] = {}

    @property
    def agent_id(self) -> AgentID:
        """Get agent ID."""
        return AgentID(str(self.id))

    @property
    def state(self) -> AgentState:
        """Get agent state."""
        return self._state

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute agent task.

        Args:
            **kwargs: Task parameters

        Returns:
            Task result
        """
        ...

    def add_capability(self, name: str, capability: AgentCapability) -> None:
        """Add a capability to the agent.

        Args:
            name: Capability name
            capability: Capability implementation
        """
        self._capabilities[name] = capability

    def get_capability(self, name: str) -> Optional[AgentCapability]:
        """Get a capability by name.

        Args:
            name: Capability name

        Returns:
            Capability implementation or None if not found
        """
        return self._capabilities.get(name)

    def list_capabilities(self) -> List[str]:
        """List all capabilities.

        Returns:
            List of capability names
        """
        return list(self._capabilities.keys())
