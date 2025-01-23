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


class PepperpyTerminator(Terminator):
    """Concrete terminator implementation for Pepperpy components."""
    
    def __init__(self):
        """Initialize the Pepperpy terminator."""
        super().__init__("pepperpy_terminator")
        self._term_steps: List[Dict[str, Any]] = []
    
    async def terminate(self, **kwargs: Any) -> None:
        """Terminate Pepperpy component.
        
        Args:
            **kwargs: Component-specific termination arguments
            
        Raises:
            TerminationError: If termination fails
        """
        if self._terminated:
            raise TerminationError("Component already terminated")
        
        try:
            # Record termination step
            self._term_steps.append({
                "step": "start",
                "kwargs": kwargs
            })
            
            # Perform termination
            # TODO: Add actual termination logic
            
            self._terminated = True
            self._term_steps.append({
                "step": "complete",
                "success": True
            })
        except Exception as e:
            self._term_steps.append({
                "step": "error",
                "error": str(e)
            })
            raise TerminationError(f"Termination failed: {str(e)}")
    
    def get_term_steps(self) -> List[Dict[str, Any]]:
        """Get termination steps.
        
        Returns:
            List of termination steps with metadata.
        """
        return self._term_steps.copy() 