"""Hub commands for the Pepperpy CLI.

This module provides commands for:
- Publishing artifacts to the Hub
- Installing artifacts from the marketplace
- Managing local artifacts
- Searching the marketplace
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from pepperpy.core.errors import PepperpyError
from pepperpy.hub.marketplace import MarketplaceConfig
from pepperpy.hub.security import SecurityManager

# Configure rich console
console = Console()


@click.group()
def hub() -> None:
    """Manage Pepperpy Hub artifacts and marketplace."""
    pass


@hub.command()
@click.argument("artifact_path", type=click.Path(exists=True))
@click.option("--public/--private", default=False, help="Make artifact public")
def publish(artifact_path: str, public: bool) -> None:
    """Publish an artifact to the Hub.

    ARTIFACT_PATH: Path to the artifact file
    """
    try:
        # Initialize components
        storage = LocalHubStorage()
        security = SecurityManager()
        marketplace = MarketplaceClient(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Publish artifact
        artifact_id = asyncio.run(
            marketplace.publish_artifact(
                artifact=Path(artifact_path),
                public=public,
            )
        )

        console.print(f"Successfully published artifact: {artifact_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@hub.command()
@click.argument("artifact_id")
@click.option("--version", help="Specific version to install")
def install(artifact_id: str, version: Optional[str] = None) -> None:
    """Install an artifact from the Hub.

    ARTIFACT_ID: ID of the artifact to install
    """
    try:
        # Initialize components
        storage = LocalHubStorage()
        security = SecurityManager()
        marketplace = MarketplaceClient(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Install artifact
        asyncio.run(
            marketplace.install_artifact(
                artifact_id=artifact_id,
                version=version,
            )
        )

        console.print(f"Successfully installed artifact: {artifact_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@hub.command()
@click.option("--query", help="Search query")
@click.option("--type", "artifact_type", help="Filter by artifact type")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--page", type=int, default=1, help="Page number")
@click.option("--per-page", type=int, default=20, help="Results per page")
def search(
    query: Optional[str] = None,
    artifact_type: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> None:
    """Search for artifacts in the Hub."""
    try:
        # Initialize components
        storage = LocalHubStorage()
        security = SecurityManager()
        marketplace = MarketplaceClient(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Parse tags
        tag_list = tags.split(",") if tags else None

        # Search artifacts
        results = asyncio.run(
            marketplace.search(
                query=query or "",
                artifact_type=artifact_type,
                tags=tag_list,
                page=page,
                per_page=per_page,
            )
        )

        # Display results
        table = Table(title="Search Results")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Version")
        table.add_column("Author")
        table.add_column("Tags")

        for artifact in results["artifacts"]:
            table.add_row(
                artifact["id"],
                artifact["name"],
                artifact["type"],
                artifact["version"],
                artifact["author"],
                ", ".join(artifact.get("tags", [])),
            )

        console.print(table)
        console.print(f"\nPage {page} of {results['total_pages']}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@hub.command()
@click.argument("artifact_id")
def inspect(artifact_id: str) -> None:
    """Inspect details of an artifact.

    ARTIFACT_ID: ID of the artifact to inspect
    """
    try:
        # Initialize components
        storage = LocalHubStorage()
        security = SecurityManager()
        marketplace = MarketplaceClient(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Get artifact details and stats
        details = asyncio.run(marketplace.get_artifact(artifact_id))
        stats = asyncio.run(marketplace.get_stats(artifact_id))

        # Display details
        console.print("\n[bold]Artifact Details[/bold]")
        console.print(json.dumps(details, indent=2))

        console.print("\n[bold]Usage Statistics[/bold]")
        console.print(json.dumps(stats, indent=2))

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@hub.command()
@click.argument("artifact_id")
@click.argument("metadata_file", type=click.Path(exists=True))
def update(artifact_id: str, metadata_file: str) -> None:
    """Update artifact metadata.

    ARTIFACT_ID: ID of the artifact to update
    METADATA_FILE: Path to JSON file with new metadata
    """
    try:
        # Load metadata from file
        with open(metadata_file) as f:
            metadata = json.load(f)

        # Initialize components
        storage = LocalHubStorage()
        security = SecurityManager()
        marketplace = MarketplaceClient(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Update metadata
        asyncio.run(
            marketplace.update_metadata(
                artifact_id=artifact_id,
                metadata=metadata,
            )
        )

        console.print(f"Successfully updated metadata for: {artifact_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@hub.command()
@click.argument("artifact_id")
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
def delete(artifact_id: str, force: bool = False) -> None:
    """Delete an artifact from the Hub.

    ARTIFACT_ID: ID of the artifact to delete
    """
    try:
        if not force:
            if not click.confirm(f"Delete artifact {artifact_id}?"):
                return

        # Initialize components
        storage = LocalHubStorage()
        security = SecurityManager()
        marketplace = MarketplaceClient(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Delete artifact
        asyncio.run(marketplace.delete_artifact(artifact_id))

        console.print(f"Successfully deleted artifact: {artifact_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()
