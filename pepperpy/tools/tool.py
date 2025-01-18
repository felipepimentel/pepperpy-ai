"""Base tool interface."""

from typing import Any

from pepperpy.tools.types import ToolResult


class Tool:
    """Base tool class."""

    async def execute(self, data: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given data.

        Args:
            data: Tool input data

        Returns:
            Tool execution result containing:
                - success: Whether execution was successful
                - data: Operation result data
                - error: Error message if execution failed
        """
        raise NotImplementedError
