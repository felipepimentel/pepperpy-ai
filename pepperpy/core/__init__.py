"""Core module for Pepperpy framework.

This module provides the core functionality and interfaces for the Pepperpy framework,
including configuration management, context handling, and lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Dict, Any, Optional

# Type variables
T = TypeVar('T')
ConfigT = TypeVar('ConfigT', bound=Dict[str, Any])

class ConfigurationProvider(Protocol):
    """Protocol defining the interface for configuration providers."""
    
    @abstractmethod
    def load(self) -> ConfigT:
        """Load configuration data."""
        pass
    
    @abstractmethod
    def save(self, config: ConfigT) -> None:
        """Save configuration data."""
        pass

class ContextManager(Protocol):
    """Protocol defining the interface for context management."""
    
    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """Get the current context."""
        pass
    
    @abstractmethod
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set the current context."""
        pass
    
    @abstractmethod
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the current context with new values."""
        pass

class LifecycleManager(Protocol):
    """Protocol defining the interface for lifecycle management."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        pass
    
    @abstractmethod
    async def terminate(self) -> None:
        """Terminate the component."""
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get the current lifecycle state."""
        pass

# Export core interfaces
__all__ = [
    'ConfigurationProvider',
    'ContextManager',
    'LifecycleManager',
]
