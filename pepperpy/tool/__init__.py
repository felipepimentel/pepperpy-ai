"""
PepperPy Tool Module.

Module for tools and integrations.
"""

from pepperpy.tool.base import (
    BaseToolProvider,
    ToolConfigError,
    ToolError,
    ToolProvider,
    ToolProviderError,
)
from pepperpy.tool.registry import (
    ToolCategory,
    get_tool,
    get_tools_by_category,
    list_tools,
    register_tool,
)
from pepperpy.tool.result import ToolResult
from pepperpy.tool.tasks import APITool, GitTool, Tool

__all__ = [
    # Base classes
    "BaseToolProvider",
    "ToolProvider",
    # Errors
    "ToolError",
    "ToolProviderError",
    "ToolConfigError",
    # Tool Registry
    "ToolCategory",
    "get_tool",
    "get_tools_by_category",
    "list_tools",
    "register_tool",
    # Results
    "ToolResult",
    # Tasks
    "APITool",
    "GitTool",
    "Tool",
]
