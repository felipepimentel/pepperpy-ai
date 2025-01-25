"""Base function implementation for external function integration."""

from typing import Any, Dict, Optional

from ....tools.base import BaseTool, ToolConfig

class Function(BaseTool):
    """Base class for external function integration."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a function.
        
        Args:
            name: The name of the function
            description: Optional description of what the function does
            config: Optional configuration parameters
        """
        super().__init__(
            config=ToolConfig(
                name=name,
                description=description or "External function integration",
                parameters=config or {},
            )
        )
        
    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the function with given parameters.
        
        Args:
            input_data: Function parameters
            context: Optional execution context
            
        Returns:
            Dict containing the function results
            
        Raises:
            NotImplementedError: Subclasses must implement _execute_impl()
        """
        raise NotImplementedError("Subclasses must implement _execute_impl()")
        
    async def _setup(self) -> None:
        """Set up function resources."""
        pass
        
    async def _teardown(self) -> None:
        """Clean up function resources."""
        pass
