"""Base agent module for Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


class AgentError(PepperpyError):
    """Agent error class."""
    pass


class BaseAgent(Lifecycle, ABC):
    """Base agent class.
    
    This class defines the interface for agents in Pepperpy.
    All agents should inherit from this class.
    """
    
    def __init__(
        self,
        name: str,
        llm: Any,
        capabilities: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize agent.
        
        Args:
            name: Agent name
            llm: LLM provider instance
            capabilities: Agent capabilities
            config: Optional configuration dictionary
        """
        self._name = name
        self.llm = llm
        self.capabilities = capabilities
        self._config = config or {}
        self._is_initialized = False
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self._name
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self._config
    
    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._is_initialized
    
    @abstractmethod
    async def _setup(self) -> None:
        """Set up agent.
        
        This method should be implemented by subclasses to perform
        any necessary setup before the agent can be used.
        """
        pass
    
    @abstractmethod
    async def _teardown(self) -> None:
        """Clean up agent.
        
        This method should be implemented by subclasses to perform
        any necessary cleanup when the agent is no longer needed.
        """
        pass
    
    @abstractmethod
    async def _validate(self) -> None:
        """Validate agent configuration.
        
        This method should be implemented by subclasses to validate
        that the agent is properly configured.
        """
        pass
    
    async def initialize(self) -> None:
        """Initialize agent.
        
        This method should be called before using the agent.
        """
        if self.is_initialized:
            return
        
        try:
            await self._validate()
            await self._setup()
            self._is_initialized = True
        except Exception as e:
            raise AgentError(f"Failed to initialize agent {self.name}: {e}")
    
    async def cleanup(self) -> None:
        """Clean up agent.
        
        This method should be called when the agent is no longer needed.
        """
        if not self.is_initialized:
            return
        
        try:
            await self._teardown()
            self._is_initialized = False
        except Exception as e:
            raise AgentError(f"Failed to clean up agent {self.name}: {e}")
    
    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """Execute agent on input data.
        
        Args:
            input_data: Input data for agent
            
        Returns:
            Agent output
            
        Raises:
            AgentError: If execution fails
        """
        if not self.is_initialized:
            raise AgentError("Agent not initialized") 