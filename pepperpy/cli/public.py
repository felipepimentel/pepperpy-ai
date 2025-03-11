"""Public API for the PepperPy CLI module.

This module exports the public API for the PepperPy CLI module.
It includes the command-line interface, command classes, and utility functions.
"""

# Import core functionality
from pepperpy.cli.core import Command, create_parser, main, register_command, run_cli

# Re-export core functionality
__all__ = [
    # Core functionality
    "Command",
    "register_command",
    "create_parser",
    "run_cli",
    "main",
]

# Import commands after CLI core is set up to avoid circular imports
from pepperpy.cli.commands import InitCommand, RunCommand

# Add commands to exports
__all__ += [
    # Commands
    "InitCommand",
    "RunCommand",
]
