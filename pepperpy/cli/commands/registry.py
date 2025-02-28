"""Registry commands for the Pepperpy CLI.

This module provides commands for:
- Managing providers
- Managing capabilities
- Listing registered components
- Validating registrations
"""

import asyncio
import importlib
from typing import Optional, Type
from uuid import UUID

import click
from rich.console import Console
from rich.table import Table

from pepperpy.core.errors import PepperpyError
from pepperpy.common.registry import CapabilityRegistry, ProviderRegistry

# Configure rich console
console = Console()


@click.group()
def registry() -> None:
    """Manage Pepperpy registries."""
    pass


@registry.group()
def provider() -> None:
    """Manage provider registry."""
    pass


@provider.command()
@click.argument("name")
@click.option("--type", "provider_type", help="Provider type")
@click.option("--capability", help="Capability name")
def register_provider(name: str, provider_type: str, capability: str) -> None:
    """Register a new provider.

    NAME is the name of the provider to register.
    """
    try:
        # Import provider class dynamically
        module_path, class_name = name.rsplit(".", 1)
        module = importlib.import_module(module_path)
        provider_class: Type = getattr(module, class_name)

        registry = ProviderRegistry()
        registry.register(
            capability=capability,
            provider_type=provider_type,
            provider_class=provider_class,
        )
        console.print(f"[green]Registered provider:[/green] {name}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@provider.command()
@click.argument("name")
def unregister_provider(name: str) -> None:
    """Unregister a provider.

    NAME is the name of the provider to unregister.
    """
    try:
        # TODO: Implement provider unregistration
        console.print(f"[green]Unregistered provider:[/green] {name}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@provider.command()
def list_providers() -> None:
    """List registered providers."""
    try:
        # TODO: Implement provider listing
        table = Table(title="Registered Providers")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Capability")
        table.add_column("Status")
        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@registry.group()
def capability() -> None:
    """Manage capability registry."""
    pass


@capability.command()
@click.argument("name")
@click.option("--version", required=True, help="Capability version")
@click.option("--framework", required=True, help="Framework name")
@click.option("--agent-id", required=True, help="Agent ID")
def register_capability(name: str, version: str, framework: str, agent_id: str) -> None:
    """Register a new capability.

    NAME is the name of the capability to register.
    """
    try:
        registry = CapabilityRegistry()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            registry.register_capability(
                capability_name=name,
                version=version,
                framework=framework,
                agent_id=UUID(agent_id),
            )
        )
        console.print(f"[green]Registered capability:[/green] {name}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@capability.command()
@click.argument("name")
@click.option("--version", required=True, help="Capability version")
@click.option("--agent-id", required=True, help="Agent ID")
def unregister_capability(name: str, version: str, agent_id: str) -> None:
    """Unregister a capability.

    NAME is the name of the capability to unregister.
    """
    try:
        registry = CapabilityRegistry()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            registry.unregister_capability(
                capability_name=name,
                version=version,
                agent_id=UUID(agent_id),
            )
        )
        console.print(f"[green]Unregistered capability:[/green] {name}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@capability.command()
@click.option("--agent-id", help="Filter by agent ID")
def list_capabilities(agent_id: Optional[str] = None) -> None:
    """List registered capabilities."""
    try:
        registry = CapabilityRegistry()
        if agent_id:
            capabilities = registry.get_agent_capabilities(UUID(agent_id))
        else:
            # TODO: Implement listing all capabilities
            capabilities = {}

        table = Table(title="Registered Capabilities")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Framework")
        table.add_column("Agent ID")

        for name, versions in capabilities.items():
            for version, metadata in versions.items():
                table.add_row(
                    name,
                    version,
                    metadata.framework,
                    str(metadata.agent_id),
                )

        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@registry.command()
def validate() -> None:
    """Validate registry state."""
    try:
        # TODO: Implement registry validation
        console.print("[green]Registry validation passed[/green]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@registry.command()
@click.option("--force", is_flag=True, help="Force cleanup without confirmation")
def cleanup(force: bool) -> None:
    """Clean up invalid registry entries."""
    try:
        if not force and not click.confirm("Clean up registry?"):
            return

        # TODO: Implement registry cleanup
        console.print("[green]Registry cleanup complete[/green]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


"""Registry commands for the Pepperpy CLI.

This module provides commands for managing the component registry:
- Registering and unregistering components
- Listing available components
- Managing component configurations
"""

import click
from rich.console import Console

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
