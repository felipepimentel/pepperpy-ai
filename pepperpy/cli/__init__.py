"""Command-line interface for Pepperpy.

This module provides the CLI interface for interacting with the framework.
"""

import click

from .commands import (
    agent,
    config,
    hub,
    registry,
    run,
    tool,
    workflow,
)

__all__ = [
    "agent",
    "config",
    "hub",
    "registry",
    "run",
    "tool",
    "workflow",
]


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
