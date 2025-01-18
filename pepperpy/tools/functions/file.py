"""File system operation tools."""

import os
from typing import Any

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import JSON, ToolResult


class FileTool(Tool):
    """Tool for file operations."""

    async def execute(self, data: dict[str, Any]) -> JSON:
        """Execute file operation.

        Args:
            data: Tool input data containing:
                - operation: Operation type (read, write, delete)
                - path: File path
                - content: File content (for write operations)
                - mode: File mode (for write operations)

        Returns:
            JSON: Tool execution result containing:
                - success: Whether operation was successful
                - path: File path
                - content: File content (for read operations)
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
                ).dict()

            if operation == "read":
                if not os.path.exists(path):
                    return ToolResult(
                        success=False,
                        data={},
                        error=f"File not found: {path}",
                    ).dict()

                with open(path) as f:
                    content = f.read()

                return ToolResult(
                    success=True, data={"path": path, "content": content}
                ).dict()

            elif operation == "write":
                content = data.get("content")
                if not content:
                    return ToolResult(
                        success=False,
                        data={},
                        error="Content is required for write operation",
                    ).dict()

                mode = data.get("mode", "w")
                os.makedirs(os.path.dirname(path), exist_ok=True)

                with open(path, mode) as f:
                    f.write(content)

                return ToolResult(success=True, data={"path": path}).dict()

            elif operation == "delete":
                if os.path.exists(path):
                    os.remove(path)

                return ToolResult(success=True, data={"path": path}).dict()

            else:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Unsupported operation: {operation}",
                ).dict()

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
            ).dict()
