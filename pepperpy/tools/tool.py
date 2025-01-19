"""Base classes for tools."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ToolResult(BaseModel, Generic[T]):
    """Result from tool execution."""

    success: bool
    data: T | None = None
    error: str | None = None


class Tool(ABC):
    """Base class for tools."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize tool."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult[Any]:
        """Execute tool.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            Tool execution result
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
