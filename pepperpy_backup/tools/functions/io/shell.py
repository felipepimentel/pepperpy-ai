"""Shell command execution tools."""

import asyncio
from typing import Any

from pepperpy.tools.tool import Tool
from pepperpy.tools.types import ToolResult


class ShellTool(Tool):
    """Tool for shell command execution."""

    async def execute(self, data: dict[str, Any]) -> ToolResult:
        """Execute shell command.

        Args:
            data: Command data including:
                - command: Command to execute
                - cwd: Working directory (optional)
                - env: Environment variables (optional)

        Returns:
            Tool result with command output
        """
        try:
            command = data.get("command")
            if not command:
                return ToolResult(
                    success=False,
                    data={},
                    error="No command provided",
                )

            cwd = data.get("cwd")
            env = data.get("env", {})

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            stdout, stderr = await process.communicate()

            error_msg = None
            if process.returncode != 0:
                error_msg = f"Command failed with exit code {process.returncode}"

            return ToolResult(
                success=process.returncode == 0,
                data={
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "exit_code": process.returncode,
                },
                error=error_msg,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Failed to execute command: {e!s}",
            )
