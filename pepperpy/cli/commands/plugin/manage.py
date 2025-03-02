"""Plugin management commands for Pepperpy CLI.

This module provides commands for:
- Listing available plugins
- Enabling/disabling plugins
- Installing/uninstalling plugins
- Viewing plugin information
"""

import click
from rich.console import Console
from rich.table import Table

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.core.plugins.cli import (
    PluginRegistry,
    disable_plugin,
    discover_plugins,
    enable_plugin,
    is_plugin_enabled,
    load_plugin,
    load_plugin_config,
)

# Configure rich console
console = Console()
logger = get_logger(__name__)


@click.group()
def plugin():
    """Manage Pepperpy plugins."""
    pass


@plugin.command()
def list():
    """List available plugins."""
    try:
        plugins = discover_plugins()

        table = Table(title="Available Plugins")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Status")
        table.add_column("Description")

        registry = PluginRegistry()
        registered_plugins = registry.get_plugins()

        for plugin_id, plugin_path in plugins:
            # Load plugin info if not already loaded
            if plugin_id not in registered_plugins:
                plugin_info = load_plugin(plugin_id, plugin_path)
            else:
                plugin_info = registered_plugins[plugin_id]

            if not plugin_info:
                continue

            status = "Enabled" if is_plugin_enabled(plugin_id) else "Disabled"

            table.add_row(
                plugin_id,
                plugin_info.get("name", plugin_id),
                plugin_info.get("version", "unknown"),
                status,
                plugin_info.get("description", ""),
            )

        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@plugin.command()
@click.argument("plugin_id")
def info(plugin_id):
    """Show plugin information.

    PLUGIN_ID is the identifier of the plugin.
    """
    try:
        # Find plugin
        plugins = dict(discover_plugins())
        if plugin_id not in plugins:
            console.print(f"[red]Plugin {plugin_id} not found[/red]")
            return

        # Load plugin info
        plugin_path = plugins[plugin_id]
        plugin_info = load_plugin(plugin_id, plugin_path)
        if not plugin_info:
            console.print(f"[red]Failed to load plugin {plugin_id}[/red]")
            return

        # Load plugin config
        config = load_plugin_config(plugin_id)

        # Display plugin info
        console.print(f"[bold]Plugin: {plugin_info.get('name', plugin_id)}[/bold]")
        console.print(f"ID: {plugin_id}")
        console.print(f"Version: {plugin_info.get('version', 'unknown')}")
        console.print(
            f"Status: {'Enabled' if is_plugin_enabled(plugin_id) else 'Disabled'}"
        )
        console.print(f"Path: {plugin_path}")
        console.print(f"Description: {plugin_info.get('description', '')}")

        # Display plugin commands
        registry = PluginRegistry()
        commands = registry.get_plugin_commands(plugin_id)

        if commands:
            console.print("\n[bold]Commands:[/bold]")
            for cmd in commands:
                console.print(f"  {cmd.name}: {cmd.help}")

        # Display plugin configuration
        if config:
            console.print("\n[bold]Configuration:[/bold]")
            for key, value in config.items():
                if key != "enabled":  # Skip internal config
                    console.print(f"  {key}: {value}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@plugin.command()
@click.argument("plugin_id")
def enable(plugin_id):
    """Enable a plugin.

    PLUGIN_ID is the identifier of the plugin.
    """
    try:
        # Find plugin
        plugins = dict(discover_plugins())
        if plugin_id not in plugins:
            console.print(f"[red]Plugin {plugin_id} not found[/red]")
            return

        # Enable plugin
        if enable_plugin(plugin_id):
            console.print(f"[green]Plugin {plugin_id} enabled[/green]")
        else:
            console.print(f"[red]Failed to enable plugin {plugin_id}[/red]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@plugin.command()
@click.argument("plugin_id")
def disable(plugin_id):
    """Disable a plugin.

    PLUGIN_ID is the identifier of the plugin.
    """
    try:
        # Find plugin
        plugins = dict(discover_plugins())
        if plugin_id not in plugins:
            console.print(f"[red]Plugin {plugin_id} not found[/red]")
            return

        # Disable plugin
        if disable_plugin(plugin_id):
            console.print(f"[green]Plugin {plugin_id} disabled[/green]")
        else:
            console.print(f"[red]Failed to disable plugin {plugin_id}[/red]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@plugin.command()
@click.argument("plugin_path", type=click.Path(exists=True))
def install(plugin_path):
    """Install a plugin from a directory.

    PLUGIN_PATH is the path to the plugin directory.
    """
    try:
        # TODO: Implement plugin installation
        console.print("[yellow]Plugin installation not implemented yet[/yellow]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@plugin.command()
@click.argument("plugin_id")
@click.option("--force", is_flag=True, help="Force uninstallation without confirmation")
def uninstall(plugin_id, force):
    """Uninstall a plugin.

    PLUGIN_ID is the identifier of the plugin.
    """
    try:
        # TODO: Implement plugin uninstallation
        console.print("[yellow]Plugin uninstallation not implemented yet[/yellow]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if hasattr(e, "recovery_hint") and e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e
