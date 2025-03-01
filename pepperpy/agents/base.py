"""Base interfaces for the agents module.

This module defines the base interfaces and classes for agents in the PepperPy framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID
import logging

from pepperpy.core.common.base import ComponentConfig, Lifecycle
from pepperpy.core.metrics import MetricsManager
from pepperpy.core.common.types.base import BaseComponent
from pepperpy.core.types.enums import AgentID, AgentState


@dataclass
class AgentConfig(ComponentConfig):
    """Base configuration for agents."""

    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


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


class BaseAgent(Lifecycle, ABC):
    """Base class for all agents in the PepperPy framework."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize base agent.

        Args:
            config: Agent configuration
        """
        super().__init__()
        self.config = config
        self._logger = logging.getLogger(f"pepperpy.agents.{config.name}")
        self._metrics_manager = MetricsManager(namespace=f"agents.{config.name}")
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
    async def _initialize(self) -> None:
        """Initialize agent resources."""
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        pass

    async def initialize(self) -> None:
        """Initialize agent."""
        self._logger.info(f"Initializing agent: {self.config.name}")
        await self._metrics_manager.initialize()
        await self._initialize()
        self._logger.info(f"Agent initialized: {self.config.name}")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        self._logger.info(f"Cleaning up agent: {self.config.name}")
        await self._cleanup()
        await self._metrics_manager.cleanup()
        self._logger.info(f"Agent cleaned up: {self.config.name}")

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
