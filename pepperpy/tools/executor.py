"""Tool execution system.

This module implements secure tool execution with permission validation
and execution tracking.
"""

import asyncio
from typing import Any

from pepperpy.common.errors import PermissionError, ToolError
from pepperpy.monitoring import logger
from pepperpy.tools.base import Tool


class ToolExecutor:
    """Handles secure tool execution with permission checks."""

    def __init__(self) -> None:
        """Initialize the tool executor."""
        self._running_tools: dict[str, asyncio.Task[Any]] = {}

    async def execute(
        self,
        tool: Tool,
        user_permissions: list[str],
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a tool securely.

        Args:
            tool: Tool to execute
            user_permissions: User's permissions
            timeout: Optional execution timeout in seconds
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            PermissionError: If user lacks required permissions
            ToolError: If execution fails or times out
        """
        # Validate permissions
        if not self._check_permissions(tool.permissions, user_permissions):
            raise PermissionError(
                f"Missing required permissions: "
                f"{set(tool.permissions) - set(user_permissions)}"
            )

        # Create execution task
        task = asyncio.create_task(tool.execute(**kwargs))
        self._running_tools[tool.name] = task

        try:
            # Execute with optional timeout
            result = await asyncio.wait_for(task, timeout) if timeout else await task
            return result

        except TimeoutError as e:
            task.cancel()
            raise ToolError(f"Tool execution timed out after {timeout}s") from e

        except Exception as e:
            raise ToolError(f"Tool execution failed: {e}") from e

        finally:
            # Cleanup
            del self._running_tools[tool.name]
            logger.info(
                "Tool execution completed",
                tool_name=tool.name,
                success=not task.cancelled(),
            )

    def _check_permissions(
        self, required_permissions: list[str], user_permissions: list[str]
    ) -> bool:
        """Check if user has all required permissions.

        Args:
            required_permissions: Permissions required by the tool
            user_permissions: User's permissions

        Returns:
            True if user has all required permissions
        """
        return all(perm in user_permissions for perm in required_permissions)

    def cancel_tool(self, tool_name: str) -> None:
        """Cancel a running tool execution.

        Args:
            tool_name: Name of tool to cancel

        Raises:
            ToolError: If tool not running
        """
        if tool_name not in self._running_tools:
            raise ToolError(f"Tool '{tool_name}' not running")

        task = self._running_tools[tool_name]
        task.cancel()
        logger.info("Tool execution cancelled", tool_name=tool_name)

    @property
    def running_tools(self) -> list[str]:
        """Get names of currently running tools.

        Returns:
            List of tool names
        """
        return list(self._running_tools.keys())
