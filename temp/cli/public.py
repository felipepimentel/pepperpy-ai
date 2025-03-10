"""Public interfaces for PepperPy CLI module.

This module provides a stable public interface for the CLI functionality.
It exposes the core CLI abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.cli.core import (
    Command,
    create_parser,
    discover_commands,
    execute_command,
    get_command,
    list_commands,
    main,
    register_command,
)

# Re-export everything
__all__ = [
    # Classes
    "Command",
    # Functions
    "create_parser",
    "discover_commands",
    "execute_command",
    "get_command",
    "list_commands",
    "main",
    "register_command",
]
