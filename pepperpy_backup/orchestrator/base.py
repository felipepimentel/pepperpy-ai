"""Base orchestrator implementation."""

import logging
from typing import Any, Dict, List, Optional, Set

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle
from ..agents import BaseAgent
from ..events import Event, EventManager
from ..profile import Profile, ProfileManager


logger = logging.getLogger(__name__)


class OrchestratorError(PepperpyError):
    """Orchestrator error."""
    pass


class Orchestrator(Lifecycle):
    """Orchestrator implementation."""
    
    def __init__(
        self,
        name: str,
        profile_manager: ProfileManager,
        event_manager: EventManager,
        agents: Optional[Dict[str, BaseAgent]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize orchestrator.
        
        Args:
            name: Orchestrator name
            profile_manager: Profile manager
            event_manager: Event manager
            agents: Optional dictionary of agents
            config: Optional orchestrator configuration
        """
        super().__init__(name)
        self._profile_manager = profile_manager
        self._event_manager = event_manager
        self._agents = agents or {}
        self._config = config or {}
        
    @property
    def profile_manager(self) -> ProfileManager:
        """Return profile manager."""
        return self._profile_manager
        
    @property
    def event_manager(self) -> EventManager:
        """Return event manager."""
        return self._event_manager
        
    @property
    def agents(self) -> Dict[str, BaseAgent]:
        """Return agents."""
        return self._agents
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return orchestrator configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize orchestrator."""
        for agent in self._agents.values():
            await agent.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up orchestrator."""
        for agent in self._agents.values():
            await agent.cleanup()
            
    def add_agent(self, agent: BaseAgent) -> None:
        """Add agent.
        
        Args:
            agent: Agent to add
            
        Raises:
            OrchestratorError: If agent already exists
        """
        if agent.name in self._agents:
            raise OrchestratorError(f"Agent {agent.name} already exists")
            
        self._agents[agent.name] = agent
        
    def remove_agent(self, name: str) -> None:
        """Remove agent.
        
        Args:
            name: Agent name
            
        Raises:
            OrchestratorError: If agent does not exist
        """
        if name not in self._agents:
            raise OrchestratorError(f"Agent {name} does not exist")
            
        del self._agents[name]
        
    def get_agent(self, name: str) -> BaseAgent:
        """Get agent.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance
            
        Raises:
            OrchestratorError: If agent does not exist
        """
        if name not in self._agents:
            raise OrchestratorError(f"Agent {name} does not exist")
            
        return self._agents[name]
        
    def has_agent(self, name: str) -> bool:
        """Check if agent exists.
        
        Args:
            name: Agent name
            
        Returns:
            True if agent exists, False otherwise
        """
        return name in self._agents
        
    def get_agents_with_profile(self, profile: Profile) -> List[BaseAgent]:
        """Get agents with profile.
        
        Args:
            profile: Profile to check
            
        Returns:
            List of agents with profile
        """
        return [
            agent for agent in self._agents.values()
            if agent.profile and agent.profile.name == profile.name
        ]
        
    def get_agents_with_capability(self, capability: str) -> List[BaseAgent]:
        """Get agents with capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            List of agents with capability
        """
        return [
            agent for agent in self._agents.values()
            if agent.profile and agent.profile.has_capability(capability)
        ]
        
    def get_agents_with_goal(self, goal: str) -> List[BaseAgent]:
        """Get agents with goal.
        
        Args:
            goal: Goal to check
            
        Returns:
            List of agents with goal
        """
        return [
            agent for agent in self._agents.values()
            if agent.profile and goal in agent.profile.goals
        ]
        
    def validate(self) -> None:
        """Validate orchestrator state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Orchestrator name cannot be empty")
            
        for agent in self._agents.values():
            agent.validate() 