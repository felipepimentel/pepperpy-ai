"""CLI registry module.

This module provides the command registry for managing CLI commands.
"""

from typing import Dict, List, Optional

from pepperpy.cli.base import Command, CommandGroup
from pepperpy.cli.types import CommandLike, CommandPath
from pepperpy.core.errors import CLIError
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class CommandRegistry:
    """Registry for CLI commands.

    This class manages all available commands and their groups.
    It provides functionality for:
    - Registering commands and groups
    - Looking up commands by name
    - Command completion
    - Help text generation
    """

    _instance: Optional["CommandRegistry"] = None

    def __init__(self) -> None:
        """Initialize command registry."""
        self._root = CommandGroup("root", "Root command group")
        self._groups: Dict[str, CommandGroup] = {}

    @classmethod
    def get_instance(cls) -> "CommandRegistry":
        """Get singleton instance.

        Returns:
            CommandRegistry instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_command()
        self,
        group_name: str,
        command: Command,
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Register a command in a group.

        Args:
            group_name: Name of group to add command to
            command: Command to register
            aliases: Optional command aliases

        Raises:
            CLIError: If group not found or command conflicts
        """
        # Get or create group
        group = self._get_or_create_group(group_name)

        try:
            # Add command to group
            group.add_command(command, aliases)
            logger.info()
                "Registered command",
                extra={}
                    "group": group_name,
                    "command": command.name,
                    "aliases": aliases,
                },
            )

        except CLIError:
            raise
        except Exception as e:
            raise CLIError( from e)
            f"Failed to register command {command.name}: {e}",
                details={}
                    "group": group_name,
                    "command": command.name,
                    "aliases": aliases,
                    "error": str(e),
                },
            )

    def register_group()
        self,
        name: str,
        description: str,
        parent: Optional[str] = None,
    ) -> CommandGroup:
        """Register a command group.

        Args:
            name: Group name
            description: Group description
            parent: Optional parent group name

        Returns:
            Created command group

        Raises:
            CLIError: If group conflicts or parent not found
        """
        try:
            # Check if group exists
            if name in self._groups:
                raise CLIError(f"Group {name} already exists")

            # Create group
            group = CommandGroup(name, description)

            # Add to parent
            parent_group = self._get_group(parent) if parent else self._root
            parent_group.add_command(group)

            # Register group
            self._groups[name] = group

            logger.info()
                "Registered command group", extra={"name": name, "parent": parent}
            )
            return group

        except CLIError:
            raise
        except Exception as e:
            raise CLIError( from e)
            f"Failed to register group {name}: {e}",
                details={"name": name, "parent": parent, "error": str(e)},
            )

    def get_command(self, command_path: CommandPath) -> Optional[CommandLike]:
        """Get a command by its full path.

        Args:
            command_path: Full command path (e.g. "group subgroup command")

        Returns:
            Command or group if found, None otherwise
        """
        parts = command_path.split()
        current: CommandLike = self._root

        for part in parts:
            if isinstance(current, CommandGroup):
                next_command = current.get_command(part)
                if not next_command:
                    return None
                current = next_command
            else:
                return None

        return current

    def get_completions(self, prefix: str) -> List[str]:
        """Get completion suggestions.

        Args:
            prefix: Current input prefix

        Returns:
            List of completion suggestions
        """
        suggestions = []
        parts = prefix.split()

        if not parts:
            # Complete root commands
            return self._root.get_completions("")

        # Find current command/group
        current: Optional[CommandLike] = self._root
        for part in parts[:-1]:
            if isinstance(current, CommandGroup):
                current = current.get_command(part)
            else:
                return []

            if not current:
                return []

        # Get completions from current command/group
        if isinstance(current, CommandGroup):
            suggestions.extend(current.get_completions(parts[-1]))

        return suggestions

    def get_help(self, command_path: Optional[CommandPath] = None) -> str:
        """Get help text for a command.

        Args:
            command_path: Optional command path (e.g. "group subgroup command")

        Returns:
            Help text
        """
        if not command_path:
            return self._root.get_help()

        command = self.get_command(command_path)
        if not command:
            raise CLIError()
                f"Command not found: {command_path}",
                details={"available": self.get_completions("")},
            )

        return command.get_help()

    def _get_group(self, name: str) -> CommandGroup:
        """Get a command group by name.

        Args:
            name: Group name

        Returns:
            Command group

        Raises:
            CLIError: If group not found
        """
        if name not in self._groups:
            raise CLIError()
                f"Group not found: {name}",
                details={"available": list(self._groups.keys())},
            )
        return self._groups[name]

    def _get_or_create_group(self, name: str) -> CommandGroup:
        """Get or create a command group.

        Args:
            name: Group name

        Returns:
            Command group
        """
        if name not in self._groups:
            self.register_group(name, f"Commands for {name}")
        return self._groups[name]
