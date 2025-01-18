"""Shell command execution tools."""

import asyncio
import os
from typing import Any

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import JSON, ToolResult


class ShellTool(Tool):
    """Tool for shell command execution."""

    async def execute(self, data: dict[str, Any]) -> JSON:
        """Execute a shell command.

        Args:
            data: Tool input data containing:
                - command: Shell command to execute
                - cwd: Working directory (optional)
                - env: Environment variables (optional)

        Returns:
            JSON: Tool execution result containing:
                - success: Whether command execution was successful
                - stdout: Command standard output
                - stderr: Command standard error
                - exit_code: Command exit code
                - error: Error message if execution failed
        """
        try:
            command = data.get("command")
            if not command:
                return ToolResult(
                    success=False,
                    data={},
                    error="Command is required",
                ).dict()

            cwd = data.get("cwd", os.getcwd())
            env = data.get("env", os.environ.copy())

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            stdout, stderr = await process.communicate()

            return ToolResult(
                success=process.returncode == 0,
                data={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "exit_code": process.returncode,
                },
            ).dict()

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
            ).dict()
