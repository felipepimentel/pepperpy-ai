"""Main CLI entry point for Pepperpy.

This module provides the main CLI interface for Pepperpy,
organizing all commands into a cohesive structure.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from pepperpy.cli.commands import (
    agent,
    config,
    hub,
    registry,
    run,
    tool,
    workflow,
)
from pepperpy.core.errors import PepperpyError
from pepperpy.monitoring import logger

# Configure rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)],
)


def setup_environment() -> None:
    """Set up the CLI environment."""
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())

    # Create Pepperpy directories if needed
    home = Path.home()
    pepperpy_dir = home / ".pepperpy"
    for subdir in ["config", "hub", "logs", "cache"]:
        (pepperpy_dir / subdir).mkdir(parents=True, exist_ok=True)


@click.group()
@click.version_option()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to config file",
)
def cli(debug: bool, config: Optional[str] = None) -> None:
    """Pepperpy CLI - AI Agent Framework.

    Run 'pepperpy COMMAND --help' for command-specific help.
    """
    # Set up environment
    setup_environment()

    # Configure logging level
    if debug:
        logger.setLevel(logging.DEBUG)
        click.echo("Debug logging enabled")

    # Load config if provided
    if config:
        click.echo(f"Using config file: {config}")


# Add command groups
cli.add_command(agent.agent)
cli.add_command(config.config)
cli.add_command(hub.hub)
cli.add_command(registry.registry)
cli.add_command(run.run)
cli.add_command(tool.tool)
cli.add_command(workflow.workflow)


def main() -> None:
    """Main CLI entry point."""
    try:
        cli()
    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}")
        if "--debug" in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
