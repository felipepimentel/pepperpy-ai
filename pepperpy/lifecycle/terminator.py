"""Component termination functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class TerminationError(PepperpyError):
    """Termination error."""
    pass


class Terminator(ABC):
    """Base class for component terminators."""
    
    def __init__(self, name: str):
        """Initialize terminator.
        
        Args:
            name: Terminator name
        """
        self.name = name
        self._terminated = False
        
    @property
    def terminated(self) -> bool:
        """Get termination status."""
        return self._terminated
        
    @abstractmethod
    async def terminate(self, **kwargs: Any) -> None:
        """Terminate component.
        
        Args:
            **kwargs: Component-specific termination arguments
            
        Raises:
            TerminationError: If termination fails
        """
        pass
        
    def validate(self) -> None:
        """Validate terminator state."""
        if not self.name:
            raise ValueError("Terminator name cannot be empty") 