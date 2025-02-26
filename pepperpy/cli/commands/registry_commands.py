"""Registry commands for the Pepperpy CLI.

This module provides commands for managing the component registry:
- Registering and unregistering components
- Listing available components
- Managing component configurations
"""

import click
from rich.console import Console
from rich.table import Table

from pepperpy.core.errors import PepperpyError

console = Console()


@click.group()
def registry() -> None:
    """Manage Pepperpy component registry."""


@registry.command()
@click.argument("component_type")
@click.argument("name")
@click.option("--config", type=click.Path(exists=True), help="Component configuration")
def register(component_type: str, name: str, config: str) -> None:
    """Register a new component.

    COMPONENT_TYPE: Type of component (agent, tool, etc.)
    NAME: Name for the component
    """
    try:
        # TODO: Implement component registration
        console.print(f"Registered {component_type} component: {name}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@registry.command()
@click.argument("component_type")
@click.argument("name")
def unregister(component_type: str, name: str) -> None:
    """Unregister a component.

    COMPONENT_TYPE: Type of component (agent, tool, etc.)
    NAME: Name of the component
    """
    try:
        if not click.confirm(f"Unregister {component_type} component {name}?"):
            return

        # TODO: Implement component unregistration
        console.print(f"Unregistered {component_type} component: {name}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@registry.command()
@click.option("--type", "component_type", help="Filter by component type")
def list(component_type: str) -> None:
    """List registered components."""
    try:
        # TODO: Implement component listing
        table = Table(title="Registered Components")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Status")

        # Add dummy data for now
        table.add_row("agent", "example-agent", "active")
        table.add_row("tool", "example-tool", "active")

        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@registry.command()
@click.argument("component_type")
@click.argument("name")
def info(component_type: str, name: str) -> None:
    """Show component information.

    COMPONENT_TYPE: Type of component (agent, tool, etc.)
    NAME: Name of the component
    """
    try:
        # TODO: Implement component info display
        console.print(f"\n[bold]{component_type.title()} Component: {name}[/bold]")
        console.print("Status: active")
        console.print("Configuration: {}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()
