"""Base agent module for Pepperpy framework."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from ..core.utils.errors import PepperpyError
from ..core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class AgentError(PepperpyError):
    """Agent error class."""
    pass


class BaseAgent(Lifecycle, ABC):
    """Base class for all agents.
    
    All agents should inherit from this class and implement the required methods.
    """
    _registry: Dict[str, Type["BaseAgent"]] = {}

    @classmethod
    def register(cls, name: str) -> Any:
        """Register an agent class.
        
        Args:
            name: The name to register the agent class under.
            
        Returns:
            The decorator function.
        """
        def decorator(agent_cls: Type["BaseAgent"]) -> Type["BaseAgent"]:
            if not isinstance(agent_cls, type):
                raise TypeError("Can only register classes")
            cls._registry[name] = agent_cls
            return agent_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> Type["BaseAgent"]:
        """Get an agent class by name.
        
        Args:
            name: The name of the agent class to get.
            
        Returns:
            The agent class.
            
        Raises:
            AgentError: If the agent class is not found.
        """
        if name not in cls._registry:
            raise AgentError(f"Agent {name} not found")
        return cls._registry[name]

    def __init__(
        self,
        name: str,
        llm: Any,
        capabilities: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize base agent.
        
        Args:
            name: Agent name.
            llm: LLM provider instance.
            capabilities: Agent capabilities.
            config: Optional agent configuration.
            
        Raises:
            AgentError: If initialization fails.
        """
        super().__init__(name, config)
        
        self._llm = llm
        self._capabilities = capabilities
        
        if not self._llm:
            raise AgentError("LLM provider cannot be None")
        
        if not isinstance(self._capabilities, dict):
            raise AgentError("Capabilities must be a dictionary")
    
    @property
    def llm(self) -> Any:
        """Get LLM provider."""
        return self._llm
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return self._capabilities
    
    async def _initialize_impl(self) -> None:
        """Initialize agent implementation.
        
        Raises:
            AgentError: If initialization fails.
        """
        try:
            await self._setup()
        except Exception as e:
            raise AgentError(f"Failed to initialize agent {self.name}: {e}")
    
    async def _cleanup_impl(self) -> None:
        """Clean up agent implementation.
        
        Raises:
            AgentError: If cleanup fails.
        """
        try:
            await self._teardown()
        except Exception as e:
            raise AgentError(f"Failed to clean up agent {self.name}: {e}")
    
    async def _validate_impl(self) -> None:
        """Validate agent implementation.
        
        Raises:
            AgentError: If validation fails.
        """
        try:
            await self._validate()
        except Exception as e:
            raise AgentError(f"Failed to validate agent {self.name}: {e}")
    
    @abstractmethod
    async def _setup(self) -> None:
        """Set up agent resources.
        
        Raises:
            Exception: If setup fails.
        """
        pass
    
    @abstractmethod
    async def _teardown(self) -> None:
        """Clean up agent resources.
        
        Raises:
            Exception: If teardown fails.
        """
        pass
    
    @abstractmethod
    async def _validate(self) -> None:
        """Validate agent state.
        
        Raises:
            Exception: If validation fails.
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """Execute agent with input data.
        
        Args:
            input_data: Input data for agent execution.
            
        Returns:
            Agent execution result.
            
        Raises:
            AgentError: If execution fails.
        """
        pass 