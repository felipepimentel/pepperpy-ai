"""Code analysis and manipulation tools."""

import ast
import os
from typing import Any

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import ToolResult


class CodeTool(Tool):
    """Tool for code operations."""

    async def execute(self, data: dict[str, Any]) -> ToolResult:
        """Execute code operation.

        Args:
            data: Tool input data containing:
                - operation: Operation type (read, write, analyze)
                - path: File path
                - code: Code content (for write operations)
                - start_line: Start line number (for read operations)
                - end_line: End line number (for read operations)

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

            if operation == "read":
                start_line = data.get("start_line")
                end_line = data.get("end_line")

                with open(path) as f:
                    lines = f.readlines()

                if start_line and end_line:
                    content = "".join(lines[start_line - 1 : end_line])
                else:
                    content = "".join(lines)

                return ToolResult(
                    success=True,
                    data={"content": content},
                    error=None,
                )

            elif operation == "write":
                code = data.get("code")
                if not code:
                    return ToolResult(
                        success=False,
                        data={},
                        error="Code content is required for write operation",
                    )

                # Validate Python syntax
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    return ToolResult(
                        success=False,
                        data={},
                        error=f"Invalid Python syntax: {e}",
                    )

                # Write code to file
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(code)

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
