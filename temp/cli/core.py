"""Core functionality for the PepperPy CLI.

This module provides the core functionality for the PepperPy command-line interface,
including command registration, argument parsing, and execution.
"""

import argparse
import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from pepperpy.utils.logging import configure_logging, get_logger

# Logger for this module
logger = get_logger(__name__)

# Registry of commands
_commands: Dict[str, "Command"] = {}


class Command(ABC):
    """Base class for CLI commands.

    A command is a subcommand of the PepperPy CLI, such as "run" or "init".
    """

    name: str = ""
    description: str = ""
    help: str = ""

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser.

        Args:
            parser: The argument parser to add arguments to
        """
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: The parsed command-line arguments

        Returns:
            The exit code (0 for success, non-zero for failure)
        """
        pass


def register_command(command_class: Type[Command]) -> Type[Command]:
    """Register a command with the CLI.

    Args:
        command_class: The command class to register

    Returns:
        The command class

    Raises:
        ValueError: If a command with the same name is already registered
    """
    command = command_class()

    if not command.name:
        raise ValueError(f"Command {command_class.__name__} has no name")

    if command.name in _commands:
        raise ValueError(f"Command {command.name} is already registered")

    _commands[command.name] = command

    return command_class


def get_command(name: str) -> Optional[Command]:
    """Get a command by name.

    Args:
        name: The name of the command

    Returns:
        The command, or None if not found
    """
    return _commands.get(name)


def list_commands() -> List[Command]:
    """List all registered commands.

    Returns:
        A list of registered commands
    """
    return list(_commands.values())


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        The argument parser
    """
    parser = argparse.ArgumentParser(
        prog="pepperpy",
        description="PepperPy: A Python framework for building AI applications",
    )

    # Add global arguments
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set the log level",
    )

    parser.add_argument(
        "--log-file",
        help="Path to the log file",
    )

    # Add subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Command to execute",
    )

    # Add command-specific parsers
    for command in _commands.values():
        command_parser = subparsers.add_parser(
            command.name,
            description=command.description,
            help=command.help,
        )

        command.add_arguments(command_parser)

    return parser


def execute_command(args: argparse.Namespace) -> int:
    """Execute a command.

    Args:
        args: The parsed command-line arguments

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    if not args.command:
        return 1

    command = get_command(args.command)
    if not command:
        logger.error(f"Unknown command: {args.command}")
        return 1

    try:
        return command.execute(args)
    except Exception as e:
        logger.error(f"Error executing command {args.command}: {str(e)}")
        logger.debug("Exception details:", exc_info=True)
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    # Create the parser
    parser = create_parser()

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    configure_logging(
        level=args.log_level.upper(),
        log_file=args.log_file,
    )

    # If no command is specified, show help
    if not args.command:
        parser.print_help()
        return 0

    # Execute the command
    return execute_command(args)


def discover_commands(package_name: str) -> None:
    """Discover and register commands from a package.

    Args:
        package_name: The name of the package to discover commands from
    """
    try:
        package = importlib.import_module(package_name)

        # Get the package directory
        package_dir = os.path.dirname(package.__file__ or "")
        if not package_dir:
            logger.warning(f"Package {package_name} has no directory")
            return

        # Iterate over Python files in the package
        for filename in os.listdir(package_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{package_name}.{filename[:-3]}"

                try:
                    module = importlib.import_module(module_name)

                    # Find Command subclasses in the module
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, Command)
                            and obj is not Command
                            and not inspect.isabstract(obj)
                        ):
                            # Register the command
                            register_command(obj)
                except ImportError as e:
                    logger.warning(f"Failed to import module {module_name}: {str(e)}")
    except ImportError as e:
        logger.warning(f"Failed to import package {package_name}: {str(e)}")


if __name__ == "__main__":
    sys.exit(main())
