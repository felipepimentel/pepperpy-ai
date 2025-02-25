"""Command-line interface for Pepperpy.

This module provides the CLI interface for interacting with the framework.
"""

import click

from pepperpy.cli.agent_commands import agent
from pepperpy.cli.config_commands import config
from pepperpy.cli.hub_commands import hub
from pepperpy.cli.registry_commands import registry
from pepperpy.cli.tool_commands import tool
from pepperpy.cli.workflow_commands import workflow

__all__ = ["cli"]


@click.group()
def cli() -> None:
    """Pepperpy CLI - A powerful framework for building AI applications."""
    pass


# Register command groups
cli.add_command(agent)
cli.add_command(config)
cli.add_command(hub)
cli.add_command(registry)
cli.add_command(tool)
cli.add_command(workflow)

if __name__ == "__main__":
    cli()
