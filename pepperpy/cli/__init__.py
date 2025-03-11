"""PepperPy CLI Module.

This module provides the command-line interface for the PepperPy framework.
It includes commands for managing PepperPy projects and applications.
"""

# Import everything from public API
from pepperpy.cli.public import (
    Command,
    create_parser,
    main,
    register_command,
    run_cli,
)

# __all__ defines the public API
__all__ = [
    # Core functionality
    "Command",
    "register_command",
    "create_parser",
    "run_cli",
    "main",
]

# Import commands to register them
from pepperpy.cli.commands import InitCommand, RunCommand

# Add commands to exports
__all__ += [
    # Commands
    "InitCommand",
    "RunCommand",
]
