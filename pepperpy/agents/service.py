"""Agent service functionality."""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable, Awaitable, Union, cast

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .base.base_agent import BaseAgent
from .factory.agent_factory import AgentFactory
from .agent import Agent
from .config import AgentConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ServiceError(PepperpyError):
    """Service error."""
    pass

class ErrorHandler:
    """Helper class for error handling."""
    
    @staticmethod
    async def handle_operation(
        operation: Union[Callable[..., T], Callable[..., Awaitable[T]]],
        error_prefix: str,
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Handle operation with consistent error handling.
        
        Args:
            operation: Operation to execute (sync or async)
            error_prefix: Prefix for error message
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            ValueError: If operation fails
        """
        try:
            result = operation(*args, **kwargs)
            if isinstance(result, Awaitable):
                result = await result
            return cast(T, result)
        except Exception as e:
            logger.error(f"{error_prefix}: {str(e)}")
            raise ValueError(f"{error_prefix}: {str(e)}")

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
        await agent.cleanup()

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
        self._error_handler = ErrorHandler()
        
    @property
    def agents(self) -> Dict[str, BaseAgent]:
        """Get registered agents."""
        return self._agents
        
    async def register_agent(self, agent: BaseAgent) -> None:
        """Register agent with service."""
        self._validator.validate_unique(agent.name, self._agents)
        self._agents[agent.name] = agent
        
    async def unregister_agent(self, name: str) -> None:
        """Unregister agent from service."""
        self._validator.validate_exists(name, self._agents)
        del self._agents[name]
    
    @abstractmethod
    async def start_agent(self, name: str, **kwargs: Any) -> None:
        """Start registered agent."""
        self._validator.validate_exists(name, self._agents)
        
    @abstractmethod
    async def stop_agent(self, name: str, **kwargs: Any) -> None:
        """Stop registered agent."""
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
        """Create and register a new agent."""
        async def create_operation() -> BaseAgent:
            self._validator.validate_unique(name, self._agents)
            agent = self._factory.create_agent(agent_type, config)
            await self._lifecycle.initialize_agent(agent)
            self._agents[name] = agent
            logger.info(f"Created agent '{name}' of type '{agent_type}'")
            return agent
            
        return await self._error_handler.handle_operation(
            create_operation,
            "Failed to create agent"
        )
            
    async def get_agent(self, name: str) -> BaseAgent:
        """Get a registered agent."""
        self._validator.validate_exists(name, self._agents)
        return self._agents[name]
    
    async def delete_agent(self, name: str) -> None:
        """Delete a registered agent."""
        async def delete_operation() -> None:
            self._validator.validate_exists(name, self._agents)
            agent = self._agents[name]
            await self._lifecycle.cleanup_agent(agent)
            del self._agents[name]
            logger.info(f"Deleted agent '{name}'")
            
        await self._error_handler.handle_operation(
            delete_operation,
            "Failed to delete agent"
        )
    
    async def process(
        self,
        name: str,
        input_data: Any,
        **kwargs: Any
    ) -> Any:
        """Process input with an agent."""
        async def process_operation() -> Any:
            self._validator.validate_exists(name, self._agents)
            agent = self._agents[name]
            return await agent.process(input_data, **kwargs)
            
        return await self._error_handler.handle_operation(
            process_operation,
            "Failed to process input"
        )
    
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