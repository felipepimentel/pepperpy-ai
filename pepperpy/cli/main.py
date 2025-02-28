"""Main CLI entry point for Pepperpy.

This module provides the main CLI interface for Pepperpy,
organizing all commands into a cohesive structure.
"""

import logging
import os
import sys
from pathlib import Path

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
from pepperpy.core.plugins.cli.loader import get_plugin_commands, load_all_plugins
from pepperpy.core.common.logging import get_logger
from pepperpy.core.errors import PepperpyError

# Configure rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)],
)

# Get logger
logger = get_logger(__name__)


def setup_environment() -> None:
    """Set up the CLI environment."""
    # Add current directory to Python path
    sys.path.insert(0, os.getcwd())

    # Create Pepperpy directories if needed
    home = Path.home()
    pepperpy_dir = home / ".pepperpy"
    for subdir in ["config", "hub", "logs", "cache", "plugins"]:
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
def cli(debug: bool, config: str | None = None) -> None:
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

    # Load plugins
    try:
        plugins = load_all_plugins()
        if plugins:
            logger.debug(f"Loaded {len(plugins)} plugins")
    except Exception as e:
        logger.error(f"Failed to load plugins: {e}")


# Add command groups
cli.add_command(agent.agent)
cli.add_command(config.config)
cli.add_command(hub.hub)
cli.add_command(registry.registry)
cli.add_command(run.run)
cli.add_command(tool.tool)
cli.add_command(workflow.workflow)

# Add plugin commands
try:
    plugin_commands = get_plugin_commands()
    for plugin_id, commands in plugin_commands.items():
        for command in commands:
            cli.add_command(command)
            logger.debug(f"Added plugin command: {command.name} from {plugin_id}")
except Exception as e:
    logger.error(f"Failed to add plugin commands: {e}")


def main() -> None:
    """Main CLI entry point."""
    try:
        cli()
    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {e!s}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e!s}")
        if "--debug" in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
