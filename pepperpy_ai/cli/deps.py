"""CLI tool for managing PepperPy AI dependencies."""

import json
from typing import Dict, List, Optional

import click

from pepperpy_ai.utils import check_dependency, get_missing_dependencies


def get_provider_dependencies() -> Dict[str, List[str]]:
    """Get provider dependencies.

    Returns:
        A dictionary mapping provider names to their required packages.
    """
    return {
        "openai": ["openai"],
        "anthropic": ["anthropic"],
        "stackspot": [],  # Uses core aiohttp
        "openrouter": [],  # Uses core aiohttp
    }


def get_capability_dependencies() -> Dict[str, List[str]]:
    """Get capability dependencies.

    Returns:
        A dictionary mapping capability names to their required packages.
    """
    return {
        "rag": ["numpy", "sentence-transformers"],
        "chat": [],  # Uses provider dependencies
        "embeddings": ["numpy", "sentence-transformers"],
    }


@click.group()
def deps() -> None:
    """Manage PepperPy AI dependencies."""
    pass


@deps.command()
def check() -> None:
    """Check available providers and features."""
    providers = get_provider_dependencies()
    capabilities = get_capability_dependencies()

    click.echo("Available Providers:")
    for provider, deps in providers.items():
        available = all(check_dependency(pkg) for pkg in deps)
        status = "✓" if available else "✗"
        click.echo(f"  {status} {provider}")
        if deps:
            click.echo(f"    Required packages: {', '.join(deps)}")

    click.echo("\nAvailable Capabilities:")
    for capability, deps in capabilities.items():
        available = all(check_dependency(pkg) for pkg in deps)
        status = "✓" if available else "✗"
        click.echo(f"  {status} {capability}")
        if deps:
            click.echo(f"    Required packages: {', '.join(deps)}")


@deps.command()
@click.argument("provider")
def check_provider(provider: str) -> None:
    """Check dependencies for a specific provider."""
    providers = get_provider_dependencies()
    if provider not in providers:
        click.echo(f"Error: Unknown provider '{provider}'")
        return

    deps = providers[provider]
    missing = get_missing_dependencies(deps)

    if not deps:
        click.echo(f"Provider '{provider}' has no additional dependencies.")
    elif not missing:
        click.echo(f"All dependencies for provider '{provider}' are satisfied.")
    else:
        click.echo(f"Missing dependencies for provider '{provider}':")
        for pkg in missing:
            click.echo(f"  - {pkg}")
        click.echo("\nInstall with:")
        click.echo(f"  pip install pepperpy-ai[{provider}]")


@deps.command()
@click.argument("capability")
def check_capability(capability: str) -> None:
    """Check dependencies for a specific capability."""
    capabilities = get_capability_dependencies()
    if capability not in capabilities:
        click.echo(f"Error: Unknown capability '{capability}'")
        return

    deps = capabilities[capability]
    missing = get_missing_dependencies(deps)

    if not deps:
        click.echo(f"Capability '{capability}' has no additional dependencies.")
    elif not missing:
        click.echo(f"All dependencies for capability '{capability}' are satisfied.")
    else:
        click.echo(f"Missing dependencies for capability '{capability}':")
        for pkg in missing:
            click.echo(f"  - {pkg}")
        click.echo("\nInstall with:")
        click.echo(f"  pip install pepperpy-ai[{capability}]")


@deps.command()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def list(json_output: bool) -> None:
    """List available providers and features."""
    providers = get_provider_dependencies()
    capabilities = get_capability_dependencies()

    if json_output:
        data = {
            "providers": {
                name: {
                    "dependencies": deps,
                    "available": all(check_dependency(pkg) for pkg in deps),
                }
                for name, deps in providers.items()
            },
            "capabilities": {
                name: {
                    "dependencies": deps,
                    "available": all(check_dependency(pkg) for pkg in deps),
                }
                for name, deps in capabilities.items()
            },
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Available Providers:")
        for name, deps in providers.items():
            click.echo(f"  {name}:")
            if deps:
                click.echo(f"    Dependencies: {', '.join(deps)}")
            else:
                click.echo("    No additional dependencies")

        click.echo("\nAvailable Capabilities:")
        for name, deps in capabilities.items():
            click.echo(f"  {name}:")
            if deps:
                click.echo(f"    Dependencies: {', '.join(deps)}")
            else:
                click.echo("    No additional dependencies")


@deps.command()
@click.argument("target")
@click.option("--provider", is_flag=True, help="Install provider dependencies")
@click.option("--capability", is_flag=True, help="Install capability dependencies")
def install(target: str, provider: bool, capability: bool) -> None:
    """Install dependencies for a provider or capability."""
    if provider and capability:
        click.echo("Error: Cannot specify both --provider and --capability")
        return

    if provider:
        providers = get_provider_dependencies()
        if target not in providers:
            click.echo(f"Error: Unknown provider '{target}'")
            return
        deps = providers[target]
    elif capability:
        capabilities = get_capability_dependencies()
        if target not in capabilities:
            click.echo(f"Error: Unknown capability '{target}'")
            return
        deps = capabilities[target]
    else:
        click.echo("Error: Must specify either --provider or --capability")
        return

    missing = get_missing_dependencies(deps)
    if not deps:
        click.echo(f"No additional dependencies required for {target}")
    elif not missing:
        click.echo(f"All dependencies for {target} are already satisfied")
    else:
        click.echo(f"Installing dependencies for {target}:")
        for pkg in missing:
            click.echo(f"  - {pkg}")
        click.echo("\nRun:")
        click.echo(f"  pip install pepperpy-ai[{target}]") 