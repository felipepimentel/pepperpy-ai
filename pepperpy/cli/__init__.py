"""Command-line interface for Pepperpy.

This module provides the CLI interface for interacting with the framework.
"""

import click

from pepperpy.cli.commands.agent import agent
from pepperpy.cli.commands.config import config
from pepperpy.cli.commands.hub import hub
from pepperpy.cli.commands.registry import registry
from pepperpy.cli.commands.tool import tool
from pepperpy.cli.commands.workflow import workflow

__all__ = ["cli"]


@click.group()
def cli() -> None:
    """Pepperpy CLI - A powerful framework for building AI applications."""


# Register command groups
cli.add_command(agent)
cli.add_command(config)
cli.add_command(hub)
cli.add_command(registry)
cli.add_command(tool)
cli.add_command(workflow)

if __name__ == "__main__":
    cli()
