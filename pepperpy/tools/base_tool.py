"""Base class for all tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class ToolResult(Generic[T]):
    """Result from tool execution."""
    
    success: bool
    error: Optional[str]
    data: Optional[T]


class BaseTool(ABC):
    """Base class for all tools."""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            Result of tool execution
        """
        pass 