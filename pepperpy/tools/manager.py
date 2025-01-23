"""Tool manager implementation.

This module provides the tool manager implementation for the Pepperpy framework,
aligned with the provider system architecture.
"""

import logging
from typing import Any, Dict, Optional

from ..interfaces import Tool, ToolManager
from ..providers.base import BaseProvider
from .base import ToolConfig
from .errors import ToolError

logger = logging.getLogger(__name__)

class PepperpyToolManager(BaseProvider, ToolManager):
    """Tool manager implementation."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Dict[str, BaseProvider]] = None,
    ) -> None:
        """Initialize tool manager.
        
        Args:
            config: Optional tool manager configuration
            dependencies: Optional tool manager dependencies
        """
        super().__init__(config or {})
        self._tools: Dict[str, Tool] = {}
        self._dependencies = dependencies or {}
    
    @property
    def tools(self) -> Dict[str, Tool]:
        """Get registered tools."""
        return self._tools
    
    @property
    def dependencies(self) -> Dict[str, BaseProvider]:
        """Get tool manager dependencies."""
        return self._dependencies
    
    async def _initialize_impl(self) -> None:
        """Initialize tool manager and its dependencies."""
        # Initialize dependencies first
        for dep in self._dependencies.values():
            if not dep.is_initialized:
                await dep.initialize()
        
        # Then initialize all registered tools
        for tool in self._tools.values():
            if not tool.is_initialized:
                await tool.initialize()
    
    async def _cleanup_impl(self) -> None:
        """Clean up tool manager and its dependencies."""
        try:
            # Clean up tools first
            for tool in reversed(list(self._tools.values())):
                if tool.is_initialized:
                    await tool.cleanup()
        finally:
            # Then clean up dependencies
            for dep in reversed(list(self._dependencies.values())):
                if dep.is_initialized:
                    await dep.cleanup()
    
    def add_tool(self, tool: Tool) -> None:
        """Add tool.
        
        Args:
            tool: Tool to add
            
        Raises:
            ToolError: If tool already exists
        """
        if tool.name in self._tools:
            raise ToolError(f"Tool {tool.name} already exists")
            
        self._tools[tool.name] = tool
    
    def remove_tool(self, name: str) -> None:
        """Remove tool.
        
        Args:
            name: Tool name
            
        Raises:
            ToolError: If tool does not exist
        """
        if name not in self._tools:
            raise ToolError(f"Tool {name} does not exist")
            
        del self._tools[name]
    
    def get_tool(self, name: str) -> Tool:
        """Get tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance
            
        Raises:
            ToolError: If tool does not exist
        """
        if name not in self._tools:
            raise ToolError(f"Tool {name} does not exist")
            
        return self._tools[name]
    
    async def execute_tool(
        self,
        name: str,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute tool.
        
        Args:
            name: Tool name
            input_data: Input data
            context: Optional execution context
            
        Returns:
            Tool result
            
        Raises:
            ToolError: If tool does not exist or is not initialized
        """
        tool = self.get_tool(name)
        
        if not tool.is_initialized:
            raise ToolError(f"Tool {name} is not initialized")
            
        try:
            return await tool.execute(input_data, context)
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {str(e)}")
            raise ToolError(f"Tool execution failed: {str(e)}") 