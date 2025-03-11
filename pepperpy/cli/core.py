"""Core functionality for the PepperPy CLI.

This module provides the core functionality for the PepperPy CLI,
including the command registry, argument parsing, and command execution.
"""

import argparse
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

# Import version information to resolve linter error
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
        The command class
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
    """Create the command-line argument parser.

    Returns:
        The argument parser
    """
    parser = argparse.ArgumentParser(
        prog="pepperpy",
        description="PepperPy command-line interface",
    )

    # Add global arguments
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the PepperPy version",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the log level",
    )

    # Add command subparsers
    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to execute",
    )

    # Add commands
    for name, cls in COMMANDS.items():
        command_parser = subparsers.add_parser(
            name,
            description=cls.description,
            help=cls.help,
        )
        cls().add_arguments(command_parser)

    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    """Run the CLI.

    Args:
        args: The command-line arguments, or None to use sys.argv

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Set the log level
    if parsed_args.log_level:
        os.environ["PEPPERPY_LOG_LEVEL"] = parsed_args.log_level
        configure_logging(level=parsed_args.log_level)

    # Show version and exit
    if hasattr(parsed_args, "version") and parsed_args.version:
        try:
            # Try to get version by importing
            from pepperpy import __version__

            print(f"PepperPy {__version__}")
        except ImportError:
            # If version is not available, show unknown
            print("PepperPy (version unknown)")
        return 0

    # Run the command
    if parsed_args.command:
        if parsed_args.command in COMMANDS:
            try:
                return COMMANDS[parsed_args.command]().execute(parsed_args)
            except Exception as e:
                logger.error(f"Error executing command: {str(e)}")
                logger.debug("Exception details:", exc_info=True)
                return 1
        else:
            logger.error(f"Unknown command: {parsed_args.command}")
            return 1
    else:
        parser.print_help()
        return 0


def main() -> int:
    """Run the CLI with sys.argv.

    Returns:
        The exit code (0 for success, non-zero for failure)
    """
    return run_cli(None)


if __name__ == "__main__":
    sys.exit(main())
