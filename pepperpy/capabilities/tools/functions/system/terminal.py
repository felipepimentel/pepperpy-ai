"""Terminal command execution tool."""

import asyncio
import os
import shlex
from typing import Any

from pydantic import BaseModel

from pepperpy.tools.base_tool import BaseTool, ToolResult


class CommandResult(BaseModel):
    """Result from command execution."""

    exit_code: int
    stdout: str
    stderr: str


class TerminalTool(BaseTool):
    """Tool for executing terminal commands."""

    def __init__(self) -> None:
        """Initialize terminal tool."""
        self.cwd = os.getcwd()
        self.unsafe_commands = {
            "rm", "mv", "cp", "dd", "mkfs",
            "sudo", "su", "chown", "chmod"
        }

    async def initialize(self) -> None:
        """Initialize tool resources."""
        pass

    def is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is safe
        """
        parts = shlex.split(command)
        base_cmd = parts[0]
        
        # Check for unsafe commands
        if base_cmd in self.unsafe_commands:
            return False
            
        # Check for command chaining
        if any(c in command for c in ["&&", "||", "|", ";"]):
            return False
            
        return True

    async def execute_command(self, command: str) -> CommandResult:
        """Execute shell command.
        
        Args:
            command: Command to execute
            
        Returns:
            Command execution result
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return CommandResult(
            exit_code=process.returncode or 0,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else ""
        )

    async def execute(self, **kwargs: Any) -> ToolResult[CommandResult]:
        """Execute tool.
        
        Args:
            command: Command to execute
            
        Returns:
            Command execution result
        """
        command = kwargs.get("command")
        if not command:
            return ToolResult(
                success=False,
                error="Command is required",
                data=None
            )
            
        # Check command safety
        if not self.is_command_safe(command):
            return ToolResult(
                success=False,
                error="Command is not allowed for security reasons",
                data=None
            )
            
        try:
            result = await self.execute_command(command)
            return ToolResult(
                success=result.exit_code == 0,
                error=result.stderr if result.exit_code != 0 else None,
                data=result
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                data=None
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass 