"""CLI tool for managing dependencies."""

import click
import sys
from typing import Optional
import json

from ..utils.dependencies import (
    print_availability_report,
    verify_provider_dependencies,
    verify_feature_dependencies,
    get_installation_command,
    get_available_providers,
    get_available_features,
)

@click.group()
def deps():
    """Manage PepperPy AI dependencies."""
    pass

@deps.command()
def check():
    """Check available providers and features."""
    print_availability_report()

@deps.command()
@click.argument("provider")
def check_provider(provider: str):
    """Check dependencies for a specific provider."""
    try:
        missing = verify_provider_dependencies(provider)
        if missing:
            click.echo(
                click.style("Missing dependencies:", fg="yellow")
                + f" {', '.join(missing)}"
            )
            click.echo(
                click.style("Install with:", fg="green")
                + f" {get_installation_command(missing)}"
            )
            sys.exit(1)
        else:
            click.echo(
                click.style("✓", fg="green")
                + f" Provider '{provider}' is ready to use"
            )
    except ValueError as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        sys.exit(1)

@deps.command()
@click.argument("feature")
def check_feature(feature: str):
    """Check dependencies for a specific feature."""
    try:
        missing = verify_feature_dependencies(feature)
        if missing:
            click.echo(
                click.style("Missing dependencies:", fg="yellow")
                + f" {', '.join(missing)}"
            )
            click.echo(
                click.style("Install with:", fg="green")
                + f" {get_installation_command(missing)}"
            )
            sys.exit(1)
        else:
            click.echo(
                click.style("✓", fg="green")
                + f" Feature '{feature}' is ready to use"
            )
    except ValueError as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        sys.exit(1)

@deps.command()
@click.option("--format", type=click.Choice(["text", "json"]), default="text")
def list(format: str):
    """List available providers and features."""
    providers = get_available_providers()
    features = get_available_features()
    
    if format == "json":
        data = {
            "providers": sorted(list(providers)),
            "features": sorted(list(features))
        }
        click.echo(json.dumps(data, indent=2))
    else:
        if providers:
            click.echo("\nAvailable Providers:")
            for provider in sorted(providers):
                click.echo(f"  • {provider}")
        
        if features:
            click.echo("\nAvailable Features:")
            for feature in sorted(features):
                click.echo(f"  • {feature}")
        
        if not providers and not features:
            click.echo("\nNo optional features available.")
            click.echo("Install extras with: poetry add 'pepperpy-ai[complete]'")

@deps.command()
@click.argument("extra")
def install(extra: str):
    """Install dependencies for a provider or feature."""
    try:
        # Try as provider first
        missing = verify_provider_dependencies(extra)
        if missing:
            cmd = get_installation_command(missing)
            click.echo(f"Installing provider '{extra}' dependencies...")
            click.echo(f"Run: {cmd}")
            return
            
        # Try as feature
        missing = verify_feature_dependencies(extra)
        if missing:
            cmd = get_installation_command(missing)
            click.echo(f"Installing feature '{extra}' dependencies...")
            click.echo(f"Run: {cmd}")
            return
            
        click.echo(
            click.style("✓", fg="green")
            + f" '{extra}' dependencies are already installed"
        )
    except ValueError:
        click.echo(
            click.style("Error:", fg="red")
            + f" '{extra}' is not a valid provider or feature"
        )
        sys.exit(1)

if __name__ == "__main__":
    deps() 