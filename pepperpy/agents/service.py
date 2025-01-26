"""Agent service functionality."""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .agent import Agent
from .config import AgentConfig
from .base import BaseAgent
from .factory import AgentFactory

logger = logging.getLogger(__name__)


class ServiceError(PepperpyError):
    """Service error."""
    pass


class AgentValidator:
    """Helper class for agent validation."""
    
    @staticmethod
    def validate_name(name: str) -> None:
        """Validate agent name."""
        if not name:
            raise ValueError("Agent name cannot be empty")
    
    @staticmethod
    def validate_exists(name: str, agents: Dict[str, BaseAgent]) -> None:
        """Validate agent exists."""
        if name not in agents:
            raise ValueError(f"Agent not found: {name}")
    
    @staticmethod
    def validate_unique(name: str, agents: Dict[str, BaseAgent]) -> None:
        """Validate agent name is unique."""
        if name in agents:
            raise ValueError(f"Agent already exists: {name}")


class AgentLifecycle:
    """Helper class for agent lifecycle management."""
    
    @staticmethod
    async def initialize_agent(agent: BaseAgent) -> None:
        """Initialize an agent."""
        if not await agent.initialize():
            raise ValueError("Failed to initialize agent")
    
    @staticmethod
    async def cleanup_agent(agent: BaseAgent) -> None:
        """Clean up an agent."""
        try:
            await agent.cleanup()
        except Exception as e:
            logger.error(f"Failed to clean up agent: {str(e)}")
            raise ValueError(f"Failed to clean up agent: {str(e)}")


class AgentService(Lifecycle, ABC):
    """Base class for agent services."""
    
    def __init__(self, name: str):
        """Initialize service.
        
        Args:
            name: Service name
        """
        super().__init__()
        self.name = name
        self._agents: Dict[str, BaseAgent] = {}
        self._factory = AgentFactory()
        self._validator = AgentValidator()
        self._lifecycle = AgentLifecycle()
        
    @property
    def agents(self) -> Dict[str, BaseAgent]:
        """Get registered agents.
        
        Returns:
            Dictionary of agent name to agent instance.
        """
        return self._agents
        
    async def register_agent(self, agent: BaseAgent) -> None:
        """Register agent with service.
        
        Args:
            agent: Agent to register
            
        Raises:
            ServiceError: If agent already registered
        """
        self._validator.validate_unique(agent.name, self._agents)
        self._agents[agent.name] = agent
        
    async def unregister_agent(self, name: str) -> None:
        """Unregister agent from service.
        
        Args:
            name: Agent name
            
        Raises:
            ServiceError: If agent not registered
        """
        self._validator.validate_exists(name, self._agents)
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
        self._validator.validate_exists(name, self._agents)
        
    @abstractmethod
    async def stop_agent(self, name: str, **kwargs: Any) -> None:
        """Stop registered agent.
        
        Args:
            name: Agent name
            **kwargs: Agent-specific stop arguments
            
        Raises:
            ServiceError: If agent not registered or stop fails
        """
        self._validator.validate_exists(name, self._agents)
        
    def validate(self) -> None:
        """Validate service state."""
        super().validate()
        self._validator.validate_name(self.name)

    async def create_agent(
        self,
        name: str,
        agent_type: str,
        config: Dict[str, Any]
    ) -> BaseAgent:
        """Create and register a new agent.
        
        Args:
            name: Name for the new agent.
            agent_type: Type of agent to create.
            config: Agent configuration.
            
        Returns:
            Created agent instance.
            
        Raises:
            ValueError: If agent name already exists or creation fails.
        """
        try:
            self._validator.validate_unique(name, self._agents)
            
            # Create agent
            agent = self._factory.create_agent(agent_type, config)
            
            # Initialize agent
            await self._lifecycle.initialize_agent(agent)
            
            # Register agent
            self._agents[name] = agent
            logger.info(f"Created agent '{name}' of type '{agent_type}'")
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise ValueError(f"Failed to create agent: {str(e)}")
    
    async def get_agent(self, name: str) -> BaseAgent:
        """Get a registered agent.
        
        Args:
            name: Agent name.
            
        Returns:
            Agent instance.
            
        Raises:
            ValueError: If agent not found.
        """
        self._validator.validate_exists(name, self._agents)
        return self._agents[name]
    
    async def delete_agent(self, name: str) -> None:
        """Delete a registered agent.
        
        Args:
            name: Agent name.
            
        Raises:
            ValueError: If agent not found.
        """
        try:
            self._validator.validate_exists(name, self._agents)
            
            # Clean up agent
            agent = self._agents[name]
            await self._lifecycle.cleanup_agent(agent)
            
            # Remove from registry
            del self._agents[name]
            logger.info(f"Deleted agent '{name}'")
            
        except Exception as e:
            logger.error(f"Failed to delete agent: {str(e)}")
            raise ValueError(f"Failed to delete agent: {str(e)}")
    
    async def process(
        self,
        name: str,
        input_data: Any,
        **kwargs: Any
    ) -> Any:
        """Process input with an agent.
        
        Args:
            name: Agent name.
            input_data: Input data to process.
            **kwargs: Additional processing arguments.
            
        Returns:
            Processing result.
            
        Raises:
            ValueError: If agent not found or processing fails.
        """
        try:
            self._validator.validate_exists(name, self._agents)
            agent = self._agents[name]
            return await agent.process(input_data, **kwargs)
            
        except Exception as e:
            logger.error(f"Failed to process input: {str(e)}")
            raise ValueError(f"Failed to process input: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up all agents."""
        for name, agent in list(self._agents.items()):
            try:
                await self._lifecycle.cleanup_agent(agent)
                del self._agents[name]
                logger.info(f"Cleaned up agent '{name}'")
                
            except Exception as e:
                logger.error(f"Failed to clean up agent '{name}': {str(e)}")
                # Continue cleaning up other agents 