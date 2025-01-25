"""Tool for managing extension registry."""

import logging
from typing import Any, Dict, List, Optional

from pepperpy.tools.base import Tool, ToolResult


logger = logging.getLogger(__name__)


class RegistryTool(Tool):
    """Tool for managing extension registry."""
    
    def __init__(self):
        """Initialize registry tool."""
        super().__init__(
            name="registry",
            description="Tool for managing extension registry",
        )
        self._registry: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize tool."""
        pass
        
    async def execute(self, **kwargs: Any) -> ToolResult[Dict[str, Any]]:
        """Execute registry operation.
        
        Args:
            **kwargs: Registry operation parameters
            
        Returns:
            Tool execution result containing operation result
        """
        try:
            operation = kwargs.get("operation")
            if not operation:
                return ToolResult(
                    success=False,
                    error="Operation is required",
                )
                
            if operation == "list":
                return ToolResult(
                    success=True,
                    data={"extensions": list(self._registry.keys())},
                )
            elif operation == "register":
                name = kwargs.get("name")
                data = kwargs.get("data")
                if not name or not data:
                    return ToolResult(
                        success=False,
                        error="Name and data are required for registration",
                    )
                    
                self._registry[name] = data
                return ToolResult(
                    success=True,
                    data={"name": name},
                )
            elif operation == "unregister":
                name = kwargs.get("name")
                if not name:
                    return ToolResult(
                        success=False,
                        error="Name is required for unregistration",
                    )
                    
                if name in self._registry:
                    del self._registry[name]
                    
                return ToolResult(
                    success=True,
                    data={"name": name},
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid operation: {operation}",
                )
                
        except Exception as e:
            logger.error(f"Registry operation failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._registry.clear()
