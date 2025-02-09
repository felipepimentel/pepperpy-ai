"""Base interfaces for the tools system.

This module defines the base interfaces and protocols for the tools system,
including tool registration, execution, and permission management.
"""

from abc import ABC, abstractmethod
from typing import Protocol, TypedDict, TypeVar, runtime_checkable


class ToolParams(TypedDict, total=False):
    """Type definition for tool parameters."""

    input: str | bytes | dict[str, str | int | float | bool]
    options: dict[str, str | int | float | bool]
    context: dict[str, str | int | float | bool]


ToolResult = TypeVar(
    "ToolResult", str, bytes, dict[str, str | int | float | bool], None, covariant=True
)


@runtime_checkable
class Tool(Protocol[ToolResult]):
    """Protocol defining the interface for tools."""

    name: str
    description: str
    permissions: list[str]

    async def execute(self, **kwargs: ToolParams) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters defined in ToolParams

        Returns:
            Tool execution result of type ToolResult
        """
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
    async def execute(self, **kwargs: ToolParams) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters defined in ToolParams

        Returns:
            Tool execution result of type ToolResult

        Raises:
            ToolError: If execution fails
        """
        ...
