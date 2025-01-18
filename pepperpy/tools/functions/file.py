"""File system operation tools."""

import os
from typing import Any

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import ToolResult


class FileTool(Tool):
    """Tool for file operations."""

    async def execute(self, data: dict[str, Any]) -> ToolResult:
        """Execute file operation.

        Args:
            data: Tool input data containing:
                - operation: Operation type (read, write, delete)
                - path: File path
                - content: File content (for write operations)
                - mode: File mode (for write operations)

        Returns:
            Tool execution result containing:
                - success: Whether operation was successful
                - data: Operation result data
                - error: Error message if operation failed
        """
        try:
            operation = data.get("operation")
            path = data.get("path")

            if not operation or not path:
                return ToolResult(
                    success=False,
                    data={},
                    error="Operation and path are required",
                )

            # Validate and convert operation to string
            if not isinstance(operation, str):
                operation = str(operation)

            # Validate and convert path to string
            if not isinstance(path, str):
                path = str(path)

            if operation == "read":
                if not os.path.exists(path):
                    return ToolResult(
                        success=False,
                        data={},
                        error=f"File not found: {path}",
                    )

                with open(path) as f:
                    content = f.read()

                return ToolResult(
                    success=True,
                    data={"path": path, "content": content},
                    error=None,
                )

            elif operation == "write":
                raw_content = data.get("content")
                if raw_content is None:
                    return ToolResult(
                        success=False,
                        data={},
                        error="Content is required for write operation",
                    )
                content = str(raw_content)

                mode = data.get("mode", "w")
                os.makedirs(os.path.dirname(path), exist_ok=True)

                with open(path, mode) as f:
                    f.write(content)

                return ToolResult(
                    success=True,
                    data={"path": path},
                    error=None,
                )

            elif operation == "delete":
                if os.path.exists(path):
                    os.remove(path)

                return ToolResult(
                    success=True,
                    data={"path": path},
                    error=None,
                )

            else:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Unsupported operation: {operation}",
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
            )
