"""Base function implementation for external function integration."""

from typing import Any, Dict, Optional

class Function:
    """Base class for external function integration."""
    
    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize a function.
        
        Args:
            name: The name of the function
            description: Optional description of what the function does
        """
        self.name = name
        self.description = description
        
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the function with given parameters.
        
        Args:
            **kwargs: Function parameters
            
        Returns:
            Dict containing the function results
        """
        raise NotImplementedError("Subclasses must implement execute()")
