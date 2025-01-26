"""Tool registry implementation."""
from typing import Any, Dict, List, Optional, Type

from .base import BaseTool

class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
    
    def register(self, tool_cls: Type[BaseTool]) -> None:
        """Register a tool class."""
        name = tool_cls.__name__
        if name in self._tools:
            raise ValueError(f"Tool {name} already registered")
        self._tools[name] = tool_cls
    
    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not registered")
        
        # Remove any instances
        if name in self._instances:
            del self._instances[name]
        
        del self._tools[name]
    
    def get_tool(self, name: str, config: Optional[Dict[str, Any]] = None) -> BaseTool:
        """Get or create a tool instance."""
        if name not in self._tools:
            raise ValueError(f"Tool {name} not registered")
        
        # Return existing instance if config matches
        if name in self._instances:
            instance = self._instances[name]
            if not config or instance.config == config:
                return instance
        
        # Create new instance
        tool_cls = self._tools[name]
        instance = tool_cls(config or {})
        self._instances[name] = instance
        return instance
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools and their schemas."""
        schemas = []
        for name, tool_cls in self._tools.items():
            # Create temporary instance to get schema
            temp_instance = tool_cls({})
            schemas.append(temp_instance.get_schema())
        return schemas
    
    def clear(self) -> None:
        """Clear all registered tools and instances."""
        self._tools.clear()
        self._instances.clear() 