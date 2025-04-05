"""
PepperPy Tool Registry Module.

Registry for discovering and managing tools.
"""

from enum import Enum
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.tool.base import BaseToolProvider

logger = get_logger(__name__)


class ToolCategory(Enum):
    """Categories of tools."""

    SEARCH = "search"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    DATA_PROCESSING = "data_processing"
    COMMUNICATION = "communication"
    CODE = "code"
    SYSTEM = "system"
    OTHER = "other"


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self) -> None:
        """Initialize tool registry."""
        self._tools: dict[str, type[BaseToolProvider]] = {}
        self._instances: dict[str, BaseToolProvider] = {}
        self._categories: dict[ToolCategory, list[str]] = {
            cat: [] for cat in ToolCategory
        }
        self._metadata: dict[str, dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        tool_class: type[BaseToolProvider],
        category: ToolCategory = ToolCategory.OTHER,
        description: str = "",
        parameters_schema: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name
            tool_class: Tool class
            category: Tool category
            description: Tool description
            parameters_schema: JSON Schema for tool parameters
        """
        if name in self._tools:
            logger.warning(f"Tool {name} already registered, overwriting")

        self._tools[name] = tool_class
        self._categories[category].append(name)

        # Store metadata
        self._metadata[name] = {
            "name": name,
            "description": description,
            "category": category.value,
            "parameters_schema": parameters_schema or {},
        }

        logger.debug(f"Registered tool: {name} ({category.value})")

    def get_tool_class(self, name: str) -> type[BaseToolProvider] | None:
        """Get tool class by name.

        Args:
            name: Tool name

        Returns:
            Tool class if found, None otherwise
        """
        return self._tools.get(name)

    def get_tool(
        self, name: str, config: dict[str, Any] | None = None
    ) -> BaseToolProvider | None:
        """Get or create tool instance.

        Args:
            name: Tool name
            config: Tool configuration

        Returns:
            Tool instance if found, None otherwise
        """
        # Check if we already have an instance
        if name in self._instances:
            return self._instances[name]

        # Get the tool class
        tool_class = self.get_tool_class(name)
        if not tool_class:
            logger.warning(f"Tool not found: {name}")
            return None

        # Create and store instance
        instance = tool_class(config=config or {})
        self._instances[name] = instance
        return instance

    def get_tools_by_category(self, category: ToolCategory) -> list[dict[str, Any]]:
        """Get all tools in a category.

        Args:
            category: Tool category

        Returns:
            List of tool metadata
        """
        return [self._metadata[name] for name in self._categories[category]]

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools.

        Returns:
            List of tool metadata
        """
        return list(self._metadata.values())


# Singleton instance
tool_registry = ToolRegistry()


def register_tool(
    name: str,
    category: ToolCategory = ToolCategory.OTHER,
    description: str = "",
    parameters_schema: dict[str, Any] | None = None,
):
    """Register tool decorator.

    Args:
        name: Tool name
        category: Tool category
        description: Tool description
        parameters_schema: JSON Schema for tool parameters

    Returns:
        Decorator function
    """

    def decorator(cls: type[BaseToolProvider]) -> type[BaseToolProvider]:
        tool_registry.register_tool(
            name=name,
            tool_class=cls,
            category=category,
            description=description,
            parameters_schema=parameters_schema,
        )
        return cls

    return decorator


def get_tool(
    name: str, config: dict[str, Any] | None = None
) -> BaseToolProvider | None:
    """Get tool by name.

    Args:
        name: Tool name
        config: Tool configuration

    Returns:
        Tool instance if found, None otherwise
    """
    return tool_registry.get_tool(name, config)


def list_tools() -> list[dict[str, Any]]:
    """List all registered tools.

    Returns:
        List of tool metadata
    """
    return tool_registry.list_tools()


def get_tools_by_category(category: ToolCategory) -> list[dict[str, Any]]:
    """Get all tools in a category.

    Args:
        category: Tool category

    Returns:
        List of tool metadata
    """
    return tool_registry.get_tools_by_category(category)
