"""CLI decorators module.

This module provides decorators for defining CLI commands.
"""

import asyncio
import functools
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from pepperpy.cli.base import Command, CommandContext, CommandResult
from pepperpy.cli.registry import CommandRegistry
from pepperpy.core.errors import CLIError
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)

# Type variables
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


class CommandDecorator(Command):
    """Command implementation that wraps a function.

    This class allows using function decorators to define commands.
    It handles:
    - Converting function arguments to command context
    - Converting function return to command result
    - Error handling and logging
    """

    def __init__(
        self,
        name: str,
        description: str,
        group: str,
        aliases: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize command decorator.

        Args:
            name: Command name
            description: Command description
            group: Command group name
            aliases: Optional command aliases
            options: Optional command options
        """
        super().__init__(name, description)
        self.group = group
        self.aliases = aliases
        self.options = options or {}
        self.func: Optional[Callable[..., Any]] = None

    def __call__(self, func: F) -> F:
        """Decorate a function as a command.

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """
        self.func = func

        # Register command
        registry = CommandRegistry.get_instance()
        registry.register_command(self.group, self, self.aliases)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return cast(F, wrapper)

    async def execute(self, context: CommandContext) -> CommandResult:
        """Execute the command function.

        Args:
            context: Command context

        Returns:
            Command result

        Raises:
            CLIError: If execution fails
        """
        if not self.func:
            raise CLIError("Command function not set")

        try:
            # Convert context to function arguments
            kwargs = self._context_to_kwargs(context)

            # Execute function
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)

            # Convert result to CommandResult
            return self._convert_result(result)

        except CLIError:
            raise
        except Exception as e:
            raise CLIError(
                f"Command execution failed: {e}",
                details={
                    "command": self.name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

    def _context_to_kwargs(self, context: CommandContext) -> Dict[str, Any]:
        """Convert command context to function kwargs.

        Args:
            context: Command context

        Returns:
            Function kwargs
        """
        kwargs = {}

        # Add args if function accepts them
        if "args" in self.func.__annotations__:
            kwargs["args"] = context.args

        # Add options if function accepts them
        if "options" in self.func.__annotations__:
            kwargs["options"] = context.options

        # Add env if function accepts it
        if "env" in self.func.__annotations__:
            kwargs["env"] = context.env

        # Add config if function accepts it
        if "config" in self.func.__annotations__:
            kwargs["config"] = context.config

        return kwargs

    def _convert_result(self, result: Any) -> CommandResult:
        """Convert function result to command result.

        Args:
            result: Function result

        Returns:
            Command result
        """
        if isinstance(result, CommandResult):
            return result

        if isinstance(result, tuple):
            success, message = result
            return CommandResult(success=success, message=message)

        if isinstance(result, bool):
            return CommandResult(
                success=result,
                message="Command succeeded" if result else "Command failed",
            )

        if isinstance(result, str):
            return CommandResult(success=True, message=result)

        if isinstance(result, dict):
            return CommandResult(success=True, message="Command succeeded", data=result)

        return CommandResult(success=True, message="Command succeeded")


def command(
    name: str,
    description: str,
    group: str = "default",
    aliases: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """Decorator for defining CLI commands.

    Args:
        name: Command name
        description: Command description
        group: Command group name
        aliases: Optional command aliases
        options: Optional command options

    Returns:
        Command decorator

    Example:
        @command("hello", "Say hello", group="greetings")
        def hello(name: str) -> str:
            return f"Hello, {name}!"
    """
    return CommandDecorator(
        name=name,
        description=description,
        group=group,
        aliases=aliases,
        options=options,
    )
