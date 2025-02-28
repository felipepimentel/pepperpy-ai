"""Main CLI module.

This module provides the main entry point for the Pepperpy CLI.
It defines the command structure and configuration for all CLI commands.
"""

from typing import Optional

import click
from rich.console import Console

from pepperpy.core.errors import PepperpyError
from pepperpy.core.common.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Configure console
console = Console()


class CLIContext:
    """CLI context for sharing state between commands."""

    def __init__(self):
        """Initialize CLI context."""
        self.verbose: bool = False
        self.debug: bool = False
        self.config_path: Optional[str] = None


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


def handle_error(func):
    """Decorator for handling CLI errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PepperpyError as e:
            console.print(f"[red]Error:[/red] {e.message}")
            if e.recovery_hint:
                console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
            if e.details:
                console.print("[yellow]Details:[/yellow]")
                for key, value in e.details.items():
                    console.print(f"  {key}: {value}")
            return 1
        except Exception as e:
            console.print(f"[red]Unexpected error:[/red] {e}")
            return 1

    return wrapper


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug mode.",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file.",
)
@pass_context
def cli(ctx: CLIContext, verbose: bool, debug: bool, config: Optional[str] = None):
    """Pepperpy CLI - AI Agent Framework.

    This is the main entry point for the Pepperpy CLI.
    Use --help with any command to see its usage.
    """
    ctx.verbose = verbose
    ctx.debug = debug
    ctx.config_path = config

    if verbose:
        console.print("[yellow]Verbose mode enabled[/yellow]")
    if debug:
        console.print("[red]Debug mode enabled[/red]")
    if config:
        console.print(f"[blue]Using config file: {config}[/blue]")


@cli.group()
def agent():
    """Agent management commands."""
    pass


@agent.command()
@click.argument("name")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["assistant", "worker", "supervisor"]),
    default="assistant",
    help="Type of agent to create.",
)
@click.option(
    "--description",
    "-d",
    help="Agent description.",
)
@pass_context
@handle_error
def create(ctx: CLIContext, name: str, type: str, description: Optional[str] = None):
    """Create a new agent.

    Args:
        name: Name of the agent
        type: Type of agent (assistant, worker, supervisor)
        description: Optional agent description
    """
    console.print(f"Creating {type} agent: {name}")
    if description:
        console.print(f"Description: {description}")
    # TODO: Implement agent creation


@agent.command()
@click.option(
    "--type",
    "-t",
    type=click.Choice(["assistant", "worker", "supervisor"]),
    help="Filter by agent type.",
)
@pass_context
@handle_error
def list_agents(ctx: CLIContext, type: Optional[str] = None):
    """List available agents.

    Args:
        type: Optional agent type filter
    """
    console.print("Listing agents")
    if type:
        console.print(f"Filtering by type: {type}")
    # TODO: Implement agent listing


@cli.group()
def workflow():
    """Workflow management commands."""
    pass


@workflow.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--env",
    "-e",
    help="Environment to deploy to.",
)
@pass_context
@handle_error
def deploy(ctx: CLIContext, path: str, env: Optional[str] = None):
    """Deploy a workflow.

    Args:
        path: Path to workflow file
        env: Optional deployment environment
    """
    console.print(f"Deploying workflow: {path}")
    if env:
        console.print(f"Environment: {env}")
    # TODO: Implement workflow deployment


@workflow.command()
@click.option(
    "--status",
    "-s",
    type=click.Choice(["active", "inactive", "failed"]),
    help="Filter by workflow status.",
)
@pass_context
@handle_error
def list_workflows(ctx: CLIContext, status: Optional[str] = None):
    """List available workflows.

    Args:
        status: Optional status filter
    """
    console.print("Listing workflows")
    if status:
        console.print(f"Filtering by status: {status}")
    # TODO: Implement workflow listing


@cli.group()
def hub():
    """Hub management commands."""
    pass


@hub.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--visibility",
    "-v",
    type=click.Choice(["public", "private"]),
    default="private",
    help="Artifact visibility.",
)
@pass_context
@handle_error
def publish(ctx: CLIContext, path: str, visibility: str):
    """Publish an artifact to the hub.

    Args:
        path: Path to artifact
        visibility: Artifact visibility
    """
    console.print(f"Publishing artifact: {path}")
    console.print(f"Visibility: {visibility}")
    # TODO: Implement artifact publishing


@hub.command()
@click.argument("artifact_id")
@click.option(
    "--version",
    "-v",
    help="Specific version to install.",
)
@pass_context
@handle_error
def install(ctx: CLIContext, artifact_id: str, version: Optional[str] = None):
    """Install an artifact from the hub.

    Args:
        artifact_id: ID of the artifact to install
        version: Optional specific version
    """
    console.print(f"Installing artifact: {artifact_id}")
    if version:
        console.print(f"Version: {version}")
    # TODO: Implement artifact installation


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.argument("key")
@click.argument("value")
@pass_context
@handle_error
def set(ctx: CLIContext, key: str, value: str):
    """Set a configuration value.

    Args:
        key: Configuration key
        value: Configuration value
    """
    console.print(f"Setting config {key} = {value}")
    # TODO: Implement config setting


@config.command()
@click.argument("key")
@pass_context
@handle_error
def get(ctx: CLIContext, key: str):
    """Get a configuration value.

    Args:
        key: Configuration key
    """
    console.print(f"Getting config value for: {key}")
    # TODO: Implement config getting


if __name__ == "__main__":
    cli()
