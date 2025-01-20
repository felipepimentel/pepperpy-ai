"""Agent service functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .agent import Agent
from .config import AgentConfig


class ServiceError(PepperpyError):
    """Service error."""
    pass


class AgentService(Lifecycle, ABC):
    """Base class for agent services."""
    
    def __init__(self, name: str):
        """Initialize service.
        
        Args:
            name: Service name
        """
        super().__init__()
        self.name = name
        self._agents: Dict[str, Agent] = {}
        
    @property
    def agents(self) -> Dict[str, Agent]:
        """Get registered agents."""
        return self._agents
        
    async def register_agent(self, agent: Agent) -> None:
        """Register agent with service.
        
        Args:
            agent: Agent to register
            
        Raises:
            ServiceError: If agent already registered
        """
        if agent.name in self._agents:
            raise ServiceError(f"Agent already registered: {agent.name}")
            
        self._agents[agent.name] = agent
        
    async def unregister_agent(self, name: str) -> None:
        """Unregister agent from service.
        
        Args:
            name: Agent name
            
        Raises:
            ServiceError: If agent not registered
        """
        if name not in self._agents:
            raise ServiceError(f"Agent not registered: {name}")
            
        del self._agents[name]
        
    @abstractmethod
    async def start_agent(self, name: str, **kwargs: Any) -> None:
        """Start registered agent.
        
        Args:
            name: Agent name
            **kwargs: Agent-specific start arguments
            
        Raises:
            ServiceError: If agent not registered or start fails
        """
        if name not in self._agents:
            raise ServiceError(f"Agent not registered: {name}")
        
    @abstractmethod
    async def stop_agent(self, name: str, **kwargs: Any) -> None:
        """Stop registered agent.
        
        Args:
            name: Agent name
            **kwargs: Agent-specific stop arguments
            
        Raises:
            ServiceError: If agent not registered or stop fails
        """
        if name not in self._agents:
            raise ServiceError(f"Agent not registered: {name}")
        
    def validate(self) -> None:
        """Validate service state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Service name cannot be empty") 