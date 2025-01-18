"""Base tool interface."""

from typing import Any

from pepperpy.tools.types import JSON


class Tool:
    """Base tool class."""

    async def execute(self, data: dict[str, Any]) -> JSON:
        """Execute the tool with the given data.

        Args:
            data: Tool input data

        Returns:
            JSON: Tool execution result.
        """
        raise NotImplementedError
