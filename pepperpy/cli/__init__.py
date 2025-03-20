"""Command-line interface for PepperPy.

This module provides the command-line interface for interacting with PepperPy,
including commands for managing agents, workflows, and other framework features.

Example:
    >>> from pepperpy.cli import CLI
    >>> cli = CLI()
    >>> cli.run()
"""

from pepperpy.cli.cli import CLI

__all__ = ["CLI"]
