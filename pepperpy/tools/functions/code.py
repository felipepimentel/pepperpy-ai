"""Code analysis and manipulation tools."""

import ast
import os
from typing import Any

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import JSON, ToolResult


class CodeTool(Tool):
    """Tool for code operations."""

    async def execute(self, data: dict[str, Any]) -> JSON:
        """Execute code operation.

        Args:
            data: Tool input data containing:
                - operation: Operation type (read, write, analyze)
                - path: File path
                - code: Code content (for write operations)
                - start_line: Start line number (for read operations)
                - end_line: End line number (for read operations)

        Returns:
            JSON: Tool execution result containing:
                - success: Whether operation was successful
                - content: File content or analysis results
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
                ).dict()

            elif operation == "write":
                code = data.get("code")
                if not code:
                    return ToolResult(
                        success=False,
                        data={},
                        error="Code content is required for write operation",
                    ).dict()

                # Validate Python syntax
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    return ToolResult(
                        success=False,
                        data={},
                        error=f"Invalid Python syntax: {e}",
                    ).dict()

                # Write code to file
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(code)

                return ToolResult(
                    success=True,
                    data={"path": path},
                ).dict()

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
