"""Tool for executing terminal commands safely."""

import asyncio
import os
import shlex
from typing import Any

from pydantic import BaseModel

from pepperpy.tools.tool import Tool, ToolResult


class CommandResult(BaseModel):
    """Result from command execution."""

    exit_code: int
    stdout: str
    stderr: str


class TerminalTool(Tool):
    """Tool for executing terminal commands safely."""

    def __init__(self) -> None:
        """Initialize terminal tool."""
        self.cwd = os.getcwd()
        self.allowed_commands = {
            "ls", "pwd", "cd", "cat", "head", "tail", "grep",
            "find", "echo", "mkdir", "touch", "rm", "cp", "mv",
            "wc", "sort", "uniq", "diff", "tree", "du", "df"
        }

    async def initialize(self) -> None:
        """Initialize tool."""
        pass

    def is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is safe
        """
        # Split command and get base command
        parts = shlex.split(command)
        if not parts:
            return False
            
        base_cmd = parts[0]
        
        # Check if base command is in allowed list
        return base_cmd in self.allowed_commands

    async def execute_command(self, command: str) -> CommandResult:
        """Execute a shell command.
        
        Args:
            command: Command to execute
            
        Returns:
            Command execution result
            
        Raises:
            Exception: If command execution fails
        """
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd
        )
        
        # Wait for completion and get output
        stdout, stderr = await process.communicate()
        
        return CommandResult(
            exit_code=process.returncode,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else ""
        )

    async def execute(self, **kwargs: Any) -> ToolResult[CommandResult]:
        """Execute terminal command.
        
        Args:
            command: Command to execute
            
        Returns:
            Command execution result
        """
        command = str(kwargs.get("command", ""))
        
        try:
            # Validate command
            if not self.is_command_safe(command):
                return ToolResult(
                    success=False,
                    error=f"Command '{command}' is not allowed for security reasons"
                )
            
            # Execute command
            result = await self.execute_command(command)
            
            return ToolResult(
                success=result.exit_code == 0,
                data=result,
                error=result.stderr if result.exit_code != 0 else None
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass 