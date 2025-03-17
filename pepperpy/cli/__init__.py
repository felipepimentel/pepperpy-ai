"""PepperPy CLI Module.

This module provides the command-line interface for the PepperPy framework.
It includes commands for managing PepperPy projects and applications.
"""

import argparse
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from pepperpy.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging(level=os.environ.get("PEPPERPY_LOG_LEVEL", "INFO"))

# Logger for this module
logger = get_logger(__name__)

# Command registry
COMMANDS: Dict[str, Type["Command"]] = {}


def register_command(cls: Type["Command"]) -> Type["Command"]:
    """Register a command class.

    Args:
        cls: The command class to register

    Returns:
        The command class (for decorator usage)
    """
    COMMANDS[cls.name] = cls
    return cls


class Command(ABC):
    """Base class for CLI commands."""

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


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        The configured argument parser
    """
    # Create the main parser
    parser = argparse.ArgumentParser(
        prog="pepperpy",
        description="Command-line interface for the PepperPy framework",
    )

    # Add global arguments
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the version and exit",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to run",
        metavar="COMMAND",
    )

    # Add command-specific parsers
    for name, command_cls in COMMANDS.items():
        command_parser = subparsers.add_parser(
            name,
            help=command_cls.help,
            description=command_cls.description,
        )
        command_cls().add_arguments(command_parser)

    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    """Run the CLI with the given arguments.

    Args:
        args: The command-line arguments to parse. If None, uses sys.argv[1:].

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    try:
        # Create the parser
        parser = create_parser()

        # Parse the arguments
        parsed_args = parser.parse_args(args)

        # Import version module here to avoid circular import
        from pepperpy.version import __version__

        # Handle --version flag
        if parsed_args.command is None and parsed_args.version:
            print(f"PepperPy version {__version__}")
            return 0

        # Set verbose mode if requested
        if parsed_args.verbose:
            os.environ["PEPPERPY_LOG_LEVEL"] = "DEBUG"
            configure_logging(level="DEBUG")

        # If no command is specified, show help
        if parsed_args.command is None:
            parser.print_help()
            return 1

        # Get the command
        command_cls = COMMANDS[parsed_args.command]
        command = command_cls()

        # Execute the command
        return command.execute(parsed_args)

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.debug("Exception details:", exc_info=True)
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    return run_cli()


# Import commands after CLI core is set up to avoid circular imports
from pepperpy.cli.commands import InitCommand, RunCommand

# __all__ defines the public API
__all__ = [
    # Core functionality
    "Command",
    "register_command",
    "create_parser",
    "run_cli",
    "main",
    # Commands
    "InitCommand",
    "RunCommand",
]
