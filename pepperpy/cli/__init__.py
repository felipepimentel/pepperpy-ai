"""CLI module for Pepperpy.

This module provides the command-line interface for Pepperpy,
including commands for managing artifacts, agents, workflows,
tools, and configuration.
"""

import click

from pepperpy.cli.commands import hub


@click.group()
def cli() -> None:
    """Pepperpy command-line interface."""
    pass


# Add command groups
cli.add_command(hub)

if __name__ == "__main__":
    cli()
