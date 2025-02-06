"""Base interfaces for the tools system.

This module defines the base interfaces and protocols for the tools system,
including tool registration, execution, and permission management.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """Protocol defining the interface for tools."""

    name: str
    description: str
    permissions: list[str]

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given parameters."""
        ...


class BaseTool(ABC):
    """Base class for implementing tools."""

    def __init__(self, name: str, description: str, permissions: list[str]) -> None:
        """Initialize the tool.

        Args:
            name: Tool name
            description: Tool description
            permissions: Required permissions to use this tool
        """
        self.name = name
        self.description = description
        self.permissions = permissions

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ToolError: If execution fails
        """
        raise NotImplementedError
