"""Tool manager implementation."""

import logging
from typing import Any, Dict, List, Optional, Set

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle
from .base import Tool, ToolError


logger = logging.getLogger(__name__)


class ToolManager(Lifecycle):
    """Tool manager implementation."""
    
    def __init__(
        self,
        name: str,
        tools: Optional[Dict[str, Tool]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tool manager.
        
        Args:
            name: Tool manager name
            tools: Optional dictionary of tools
            config: Optional tool manager configuration
        """
        super().__init__(name)
        self._tools = tools or {}
        self._config = config or {}
        
    @property
    def tools(self) -> Dict[str, Tool]:
        """Return tools."""
        return self._tools
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return tool manager configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize tool manager."""
        for tool in self._tools.values():
            await tool.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up tool manager."""
        for tool in self._tools.values():
            await tool.cleanup()
            
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
        
    def has_tool(self, name: str) -> bool:
        """Check if tool exists.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools
        
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
            Execution result
            
        Raises:
            ToolError: If tool does not exist
        """
        tool = self.get_tool(name)
        return await tool.execute(input_data, context)
        
    def validate(self) -> None:
        """Validate tool manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Tool manager name cannot be empty")
            
        for tool in self._tools.values():
            tool.validate() 