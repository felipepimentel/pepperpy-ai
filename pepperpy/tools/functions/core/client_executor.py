"""Client executor for managing function execution."""

from typing import Any, Dict, List, Optional

from ....tools.base import BaseTool, ToolConfig

class ClientExecutor(BaseTool):
    """Manages execution of functions for clients."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the client executor.
        
        Args:
            name: Tool name
            config: Optional configuration
        """
        super().__init__(
            config=ToolConfig(
                name=name,
                description="Tool for managing function execution",
                parameters=config or {},
            )
        )
        self._functions: Dict[str, BaseTool] = {}
        
    def register(self, function: BaseTool) -> None:
        """Register a function for execution.
        
        Args:
            function: The function to register
        """
        self._functions[function.name] = function
        
    async def _execute_impl(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a registered function.
        
        Args:
            input_data: Input data containing function name and parameters
            context: Optional execution context
            
        Returns:
            Dict containing the function results
            
        Raises:
            ValueError: If function is not registered or parameters are invalid
        """
        name = input_data.get("name")
        if not name:
            raise ValueError("Function name is required")
            
        if name not in self._functions:
            raise ValueError(f"Function {name} not registered")
            
        params = input_data.get("params", {})
        return await self._functions[name].execute(params, context)
        
    def list_functions(self) -> List[Dict[str, Optional[str]]]:
        """List all registered functions.
        
        Returns:
            List of dicts containing function names and descriptions
        """
        return [
            {"name": name, "description": func.description}
            for name, func in self._functions.items()
        ]
        
    async def _setup(self) -> None:
        """Set up tool resources."""
        # Initialize all registered functions
        for function in self._functions.values():
            if not function.is_initialized:
                await function.initialize()
                
    async def _teardown(self) -> None:
        """Clean up tool resources."""
        # Clean up all registered functions
        for function in self._functions.values():
            if function.is_initialized:
                await function.cleanup()
        self._functions.clear()
