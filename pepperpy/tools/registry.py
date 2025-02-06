"""Tool registry system.

This module implements the tool registry system for managing and accessing tools.
"""

from typing import Any

from pepperpy.common.errors import ToolError
from pepperpy.tools.base import Tool


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool.

        Args:
            tool: Tool instance to register

        Raises:
            ToolError: If tool with same name already exists
        """
        if tool.name in self._tools:
            raise ToolError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool.

        Args:
            tool_name: Name of tool to unregister

        Raises:
            ToolError: If tool not found
        """
        if tool_name not in self._tools:
            raise ToolError(f"Tool '{tool_name}' not found")
        del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Tool:
        """Get a registered tool by name.

        Args:
            tool_name: Name of tool to get

        Returns:
            Tool instance

        Raises:
            ToolError: If tool not found
        """
        if tool_name not in self._tools:
            raise ToolError(f"Tool '{tool_name}' not found")
        return self._tools[tool_name]

    def list_tools(self, permissions: list[str] | None = None) -> list[Tool]:
        """List all registered tools, optionally filtered by permissions.

        Args:
            permissions: Optional list of permissions to filter by

        Returns:
            List of tool instances
        """
        if permissions is None:
            return list(self._tools.values())

        return [
            tool
            for tool in self._tools.values()
            if all(perm in permissions for perm in tool.permissions)
        ]

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ToolError: If tool not found or execution fails
        """
        tool = self.get_tool(tool_name)
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            raise ToolError(f"Tool execution failed: {e}") from e
