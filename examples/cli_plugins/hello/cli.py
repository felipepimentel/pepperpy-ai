"""CLI commands for the Hello plugin."""

import click
from rich.console import Console

# Plugin metadata
PLUGIN_INFO = {
    "name": "Hello Plugin",
    "version": "0.1.0",
    "description": "A simple example plugin for Pepperpy CLI",
    "author": "Pepperpy Team",
}

# Configure rich console
console = Console()


@click.command()
@click.argument("name", default="World")
def hello(name: str) -> None:
    """Say hello to someone.

    NAME is the name to greet (default: "World").
    """
    console.print(f"[green]Hello, {name}![/green]")


@click.group()
def greet() -> None:
    """Greeting commands."""
    pass


@greet.command()
@click.argument("name", default="World")
def hi(name: str) -> None:
    """Say hi to someone.

    NAME is the name to greet (default: "World").
    """
    console.print(f"[blue]Hi, {name}![/blue]")


@greet.command()
@click.argument("name", default="World")
def bye(name: str) -> None:
    """Say goodbye to someone.

    NAME is the name to say goodbye to (default: "World").
    """
    console.print(f"[yellow]Goodbye, {name}![/yellow]")
