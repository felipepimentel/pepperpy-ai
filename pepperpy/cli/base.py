"""CLI base module.

This module provides the base classes and decorators for the CLI system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pepperpy.core.errors import CLIError
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


@dataclass
class CommandContext:
    """Context for command execution.

    Attributes:
        args: Command arguments
        options: Command options
        env: Environment variables
        config: Configuration values
    """

    args: List[str]
    options: Dict[str, Any]
    env: Dict[str, str]
    config: Dict[str, Any]


@dataclass
class CommandResult:
    """Result of command execution.

    Attributes:
        success: Whether the command succeeded
        message: Output message
        data: Optional result data
        error: Optional error details
    """

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class Command(ABC):
    """Base class for CLI commands.

    This class defines the interface that all commands must implement.
    Commands are responsible for:
    - Validating input
    - Executing business logic
    - Handling errors
    - Providing help and completion
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize command.

        Args:
            name: Command name
            description: Command description
        """
        self.name = name
        self.description = description
        self._parent: Optional["CommandGroup"] = None

    @property
    def parent(self) -> Optional["CommandGroup"]:
        """Get parent command group."""
        return self._parent

    @parent.setter
    def parent(self, parent: "CommandGroup") -> None:
        """Set parent command group."""
        self._parent = parent

    @property
    def full_name(self) -> str:
        """Get full command name including parent groups."""
        if self.parent:
            return f"{self.parent.full_name} {self.name}"
        return self.name

    async def validate(self, context: CommandContext) -> None:
        """Validate command input.

        Args:
            context: Command context

        Raises:
            CLIError: If validation fails
        """
        pass

    @abstractmethod
    async def execute(self, context: CommandContext) -> CommandResult:
        """Execute the command.

        Args:
            context: Command context

        Returns:
            Command result

        Raises:
            CLIError: If execution fails
        """
        pass

    def get_help(self) -> str:
        """Get command help text.

        Returns:
            Help text
        """
        return self.description

    def get_completions(self, prefix: str) -> List[str]:
        """Get command completion suggestions.

        Args:
            prefix: Current input prefix

        Returns:
            List of completion suggestions
        """
        return []


class CommandGroup(Command):
    """Group of related commands.

    This class allows organizing commands into hierarchical groups.
    Groups can contain both commands and other groups.
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize command group.

        Args:
            name: Group name
            description: Group description
        """
        super().__init__(name, description)
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}

    def add_command()
        self, command: Command, aliases: Optional[List[str]] = None
    ) -> None:
        """Add a command to the group.

        Args:
            command: Command to add
            aliases: Optional command aliases

        Raises:
            CLIError: If command name conflicts
        """
        if command.name in self._commands:
            raise CLIError()
                f"Command {command.name} already exists in group {self.name}"
            )

        command.parent = self
        self._commands[command.name] = command

        # Add aliases
        if aliases:
            for alias in aliases:
                if alias in self._aliases:
                    raise CLIError(f"Alias {alias} already exists in group {self.name}")
                self._aliases[alias] = command.name

    def get_command(self, name: str) -> Optional[Command]:
        """Get a command by name.

        Args:
            name: Command name or alias

        Returns:
            Command if found, None otherwise
        """
        # Check aliases first
        if name in self._aliases:
            name = self._aliases[name]

        return self._commands.get(name)

    def list_commands(self) -> List[Command]:
        """List all commands in the group.

        Returns:
            List of commands
        """
        return list(self._commands.values())

    async def execute(self, context: CommandContext) -> CommandResult:
        """Execute a subcommand.

        Args:
            context: Command context

        Returns:
            Command result

        Raises:
            CLIError: If subcommand not found or execution fails
        """
        if not context.args:
            return CommandResult()
                success=False,
                message=f"Missing subcommand for {self.name}",
                error={"type": "missing_subcommand"},
            )

        subcommand_name = context.args[0]
        subcommand = self.get_command(subcommand_name)

        if not subcommand:
            return CommandResult()
                success=False,
                message=f"Unknown subcommand: {subcommand_name}",
                error={}
                    "type": "unknown_subcommand",
                    "name": subcommand_name,
                    "available": list(self._commands.keys()),
                },
            )

        # Update context for subcommand
        subcontext = CommandContext()
            args=context.args[1:],
            options=context.options,
            env=context.env,
            config=context.config,
        )

        try:
            # Validate and execute subcommand
            await subcommand.validate(subcontext)
            return await subcommand.execute(subcontext)

        except CLIError:
            raise
        except Exception as e:
            raise CLIError( from e)
            f"Failed to execute {subcommand.name}: {e}",
                details={}
                    "command": subcommand.name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

    def get_help(self) -> str:
        """Get group help text.

        Returns:
            Help text including subcommands
        """
        lines = [self.description, "", "Available commands:"]

        for command in sorted(self._commands.values(), key=lambda c: c.name):
            lines.append(f"  {command.name:20} {command.description}")

        if self._aliases:
            lines.extend(["", "Aliases:"])
            for alias, name in sorted(self._aliases.items()):
                lines.append(f"  {alias:20} -> {name}")

        return "\n".join(lines)

    def get_completions(self, prefix: str) -> List[str]:
        """Get completion suggestions.

        Args:
            prefix: Current input prefix

        Returns:
            List of completion suggestions
        """
        suggestions = []

        # Add command names
        for name in self._commands:
            if name.startswith(prefix):
                suggestions.append(name)

        # Add aliases
        for alias in self._aliases:
            if alias.startswith(prefix):
                suggestions.append(alias)

        return suggestions
