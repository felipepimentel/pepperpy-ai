"""Agent builder functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pepperpy.common.errors import PepperpyError
from .agent import Agent
from .config import AgentConfig
from .types import AgentCapability


class BuilderError(PepperpyError):
    """Builder error."""
    pass


class AgentBuilder(ABC):
    """Base class for agent builders."""
    
    def __init__(self, name: str):
        """Initialize builder.
        
        Args:
            name: Builder name
        """
        self.name = name
        self._config: Optional[AgentConfig] = None
        self._capabilities: Dict[str, Type[AgentCapability]] = {}
        
    def with_config(self, config: AgentConfig) -> "AgentBuilder":
        """Set agent configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            Builder instance for chaining
        """
        config.validate()
        self._config = config
        return self
        
    def with_capability(
        self, name: str, capability: Type[AgentCapability]
    ) -> "AgentBuilder":
        """Add agent capability.
        
        Args:
            name: Capability name
            capability: Capability class
            
        Returns:
            Builder instance for chaining
            
        Raises:
            BuilderError: If capability already exists
        """
        if name in self._capabilities:
            raise BuilderError(f"Capability already exists: {name}")
            
        self._capabilities[name] = capability
        return self
        
    @abstractmethod
    async def build(self) -> Agent:
        """Build agent instance.
        
        Returns:
            Built agent instance
            
        Raises:
            BuilderError: If build fails
        """
        if not self._config:
            raise BuilderError("Agent configuration not set")
            
        # Validate capabilities
        for cap_config in self._config.capabilities:
            if cap_config.name not in self._capabilities:
                raise BuilderError(
                    f"Capability not registered: {cap_config.name}"
                )
        
    def validate(self) -> None:
        """Validate builder state."""
        if not self.name:
            raise ValueError("Builder name cannot be empty") 