"""Agent type definitions and protocols."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.common.errors import PepperpyError


class AgentError(PepperpyError):
    """Agent error."""
    pass


@dataclass
class AgentConfig:
    """Agent configuration."""
    
    name: str
    description: str
    capabilities: List[str]
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]


class AgentState(Protocol):
    """Agent state protocol."""
    
    @property
    def initialized(self) -> bool:
        """Get initialization status."""
        ...
        
    @property
    def running(self) -> bool:
        """Get running status."""
        ...
        
    @property
    def paused(self) -> bool:
        """Get paused status."""
        ...
        
    @property
    def stopped(self) -> bool:
        """Get stopped status."""
        ...


class AgentContext(Protocol):
    """Agent context protocol."""
    
    @property
    def state(self) -> AgentState:
        """Get agent state."""
        ...
        
    @property
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        ...
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get context metadata."""
        ...


class AgentCapability(Protocol):
    """Agent capability protocol."""
    
    @property
    def name(self) -> str:
        """Get capability name."""
        ...
        
    @property
    def description(self) -> str:
        """Get capability description."""
        ...
        
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute capability.
        
        Args:
            **kwargs: Capability-specific arguments
            
        Returns:
            Capability execution result
            
        Raises:
            AgentError: If execution fails
        """
        ...


__all__ = [
    "AgentError",
    "AgentConfig",
    "AgentState",
    "AgentContext",
    "AgentCapability",
] 