"""Component initialization functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class InitializationError(PepperpyError):
    """Initialization error."""
    pass


class Initializer(ABC):
    """Base class for component initializers."""
    
    def __init__(self, name: str):
        """Initialize initializer.
        
        Args:
            name: Initializer name
        """
        self.name = name
        self._initialized = False
        
    @property
    def initialized(self) -> bool:
        """Get initialization status."""
        return self._initialized
        
    @abstractmethod
    async def initialize(self, **kwargs: Any) -> None:
        """Initialize component.
        
        Args:
            **kwargs: Component-specific initialization arguments
            
        Raises:
            InitializationError: If initialization fails
        """
        pass
        
    def validate(self) -> None:
        """Validate initializer state."""
        if not self.name:
            raise ValueError("Initializer name cannot be empty") 