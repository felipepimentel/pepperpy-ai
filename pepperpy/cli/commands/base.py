"""Base classes for CLI commands.

This module provides base classes and utilities for implementing CLI commands.
"""

import abc
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

import click
from rich.console import Console

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

# Configure rich console
console = Console()
logger = get_logger(__name__)

# Type definitions
CommandCallback = Callable[..., Any]
T = TypeVar("T", bound="BaseCommand")


class BaseCommand(abc.ABC):
    """Base class for CLI commands.

    This class provides common functionality for CLI commands,
    including error handling and logging.
    """

    name: str
    help: str
    
    @classmethod
    def as_click_command(cls: Type[T]) -> click.Command:
        """Convert this command to a Click command.

        Returns:
            Click command
        """
        @click.command(name=cls.name, help=cls.help)
        @click.pass_context
        def command(ctx: click.Context, **kwargs: Any) -> Any:
            """Command wrapper."""
            try:
                cmd = cls()
                return cmd.execute(**kwargs)
            except PepperpyError as e:
                console.print(f"[red]Error:[/red] {str(e)}")
                if hasattr(e, "recovery_hint") and e.recovery_hint:
                    console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
                raise click.Abort()
            except Exception as e:
                console.print(f"[red]Unexpected error:[/red] {str(e)}")
                if ctx.obj and ctx.obj.get("debug"):
                    console.print_exception()
                raise click.Abort()
                
        # Add parameters
        for param in cls.get_parameters():
            command = param(command)
            
        return cast(click.Command, command)
    
    @classmethod
    def get_parameters(cls) -> List[Callable[[CommandCallback], CommandCallback]]:
        """Get command parameters.

        Returns:
            List of Click parameter decorators
        """
        return []
    
    @abc.abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the command.

        Args:
            **kwargs: Command arguments

        Returns:
            Command result
        """
        pass


class BaseCommandGroup(abc.ABC):
    """Base class for CLI command groups.

    This class provides common functionality for CLI command groups,
    including error handling and logging.
    """

    name: str
    help: str
    commands: List[Type[BaseCommand]] = []
    
    @classmethod
    def as_click_group(cls) -> click.Group:
        """Convert this command group to a Click group.

        Returns:
            Click group
        """
        @click.group(name=cls.name, help=cls.help)
        @click.pass_context
        def group(ctx: click.Context, **kwargs: Any) -> None:
            """Group wrapper."""
            # Store context
            if not ctx.obj:
                ctx.obj = {}
            ctx.obj.update(kwargs)
                
        # Add commands
        for command_cls in cls.commands:
            group.add_command(command_cls.as_click_command())
            
        return cast(click.Group, group) 