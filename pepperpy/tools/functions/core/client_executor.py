"""Client executor for managing function execution."""

from typing import Any, Dict, List, Optional

from .function import Function

class ClientExecutor:
    """Manages execution of functions for clients."""
    
    def __init__(self):
        """Initialize the client executor."""
        self._functions: Dict[str, Function] = {}
        
    def register(self, function: Function) -> None:
        """Register a function for execution.
        
        Args:
            function: The function to register
        """
        self._functions[function.name] = function
        
    async def execute(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a registered function.
        
        Args:
            name: Name of the function to execute
            **kwargs: Function parameters
            
        Returns:
            Dict containing the function results
            
        Raises:
            KeyError: If function is not registered
        """
        if name not in self._functions:
            raise KeyError(f"Function {name} not registered")
            
        return await self._functions[name].execute(**kwargs)
        
    def list_functions(self) -> List[Dict[str, Optional[str]]]:
        """List all registered functions.
        
        Returns:
            List of dicts containing function names and descriptions
        """
        return [
            {"name": name, "description": func.description}
            for name, func in self._functions.items()
        ]
