"""CLI package for Pepperpy.

This package provides the command-line interface for Pepperpy,
with a pluggable architecture for different modules.
"""

from typing import Dict, Type

import click

from pepperpy.monitoring import bind_logger

# Configure logger
logger = bind_logger(module="cli")


class CommandGroup:
    """Base class for CLI command groups."""

    name: str
    help: str

    @classmethod
    def get_command_group(cls) -> click.Group:
        """Get the Click command group for this module."""
        raise NotImplementedError


class CLIManager:
    """Manages CLI command groups and plugins."""

    _groups: Dict[str, Type[CommandGroup]] = {}

    @classmethod
    def register_group(cls, group: Type[CommandGroup]) -> None:
        """Register a command group.

        Args:
        ----
            group: The command group class to register.

        """
        cls._groups[group.name] = group

    @classmethod
    def create_cli(cls) -> click.Group:
        """Create the main CLI group with all registered commands.

        Returns
        -------
            click.Group: The main CLI command group.

        """

        @click.group()
        def cli():
            """Pepperpy CLI - AI Agent Framework."""
            pass

        # Add all registered command groups
        for group_cls in cls._groups.values():
            cli.add_command(group_cls.get_command_group())

        return cli


# Create the main CLI
cli = CLIManager.create_cli()
