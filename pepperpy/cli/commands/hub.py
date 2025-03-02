"""Hub commands for the Pepperpy CLI.
from typing import Optional
import click
from rich.console import Console

This module provides commands for:
- Publishing artifacts to the Hub
- Installing artifacts from the marketplace
- Managing local artifacts
- Searching the marketplace
"""

import asyncio
import json
from pathlib import Path
from typing import LocalHubStorage  # TODO: Verificar se este é o import correto
from typing import MarketplaceClient  # TODO: Verificar se este é o import correto
from typing import (
    Optional,
    Set,
)

import click
from rich.console import Console
from rich.table import Table

from pepperpy.core.errors import PepperpyError
from pepperpy.hub.marketplace import MarketplaceConfig, MarketplaceManager
from pepperpy.hub.publishing import Publisher
from pepperpy.hub.security import SecurityConfig, SecurityManager
from pepperpy.hub.storage.local import LocalStorageBackend

# Configure rich console
console = Console()


@click.group()
def hub() -> None:
    """Manage Pepperpy Hub artifacts and marketplace."""
    pass


@hub.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", help="Artifact name")
@click.option("--version", help="Artifact version")
@click.option("--type", "artifact_type", help="Artifact type")
@click.option("--description", help="Artifact description")
@click.option("--author", help="Artifact author")
@click.option("--tag", "tags", multiple=True, help="Artifact tags")
@click.option(
    "--visibility",
    type=click.Choice(["public", "private", "shared"]),
    default="public",
    help="Artifact visibility",
)
def publish(
    path: str,
    name: Optional[str] = None,
    version: Optional[str] = None,
    artifact_type: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None,
    tags: Optional[Set[str]] = None,
    visibility: str = "public",
) -> None:
    """Publish an artifact to the Hub.

    PATH is the path to the artifact file or directory.
    """
    try:
        # Load artifact content
        path_obj = Path(path)
        if path_obj.is_file():
            with open(path_obj) as f:
                content = json.load(f)
        else:
            raise click.BadParameter("Only file artifacts are supported currently")

        # Initialize components
        storage = LocalStorageBackend()
        security = SecurityManager(SecurityConfig())
        marketplace = MarketplaceManager(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )
        publisher = Publisher(
            storage=storage,
            security=security,
            marketplace=marketplace,
        )

        # Extract metadata from content if not provided
        if not name:
            name = content.get("name")
        if not version:
            version = content.get("version", "1.0.0")
        if not artifact_type:
            artifact_type = content.get("type")
        if not description:
            description = content.get("description", "")
        if not author:
            author = content.get("author", "")

        # Validate required fields
        if not name:
            raise click.BadParameter("Artifact name is required")
        if not artifact_type:
            raise click.BadParameter("Artifact type is required")
        if not version:
            raise click.BadParameter("Version is required")
        if not description:
            raise click.BadParameter("Description is required")

        # Run async publish in event loop
        loop = asyncio.get_event_loop()
        artifact_id, marketplace_id = loop.run_until_complete(
            publisher.publish(
                name=name,
                version=version,
                artifact_type=artifact_type,
                content=content,
                description=description,
                author=author or "",  # Make author optional
                tags=set(tags) if tags else set(),
                visibility=visibility,
            )
        )

        console.print(
            f"[green]Successfully published artifact:[/green] {name}@{version}"
        )
        console.print(f"Artifact ID: {artifact_id}")
        console.print(f"Marketplace ID: {marketplace_id}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@hub.command()
@click.argument("artifact_id")
@click.option("--version", help="Specific version to install")
def install(artifact_id: str, version: Optional[str] = None) -> None:
    """Install an artifact from the marketplace.

    ARTIFACT_ID is the ID of the artifact to install.
    """
    try:
        # Initialize components
        storage = LocalStorageBackend()
        security = SecurityManager(SecurityConfig())
        marketplace = MarketplaceManager(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Run async install in event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            marketplace.install_artifact(
                artifact_id=artifact_id,
                version=version,
            )
        )

        console.print(f"[green]Successfully installed artifact:[/green] {artifact_id}")
        if version:
            console.print(f"Version: {version}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@hub.command()
@click.argument("query", required=False)
@click.option("--type", "artifact_type", help="Filter by artifact type")
@click.option("--tag", "tags", multiple=True, help="Filter by tags")
@click.option("--page", type=int, default=1, help="Page number")
@click.option("--per-page", type=int, default=20, help="Results per page")
def search(
    query: Optional[str] = None,
    artifact_type: Optional[str] = None,
    tags: Optional[Set[str]] = None,
    page: int = 1,
    per_page: int = 20,
) -> None:
    """Search for artifacts in the marketplace.

    QUERY is an optional search query.
    """
    try:
        # Initialize components
        storage = LocalStorageBackend()
        security = SecurityManager(SecurityConfig())
        marketplace = MarketplaceManager(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Run async search in event loop
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            marketplace.search(
                query=query or "",
                artifact_type=artifact_type,
                tags=list(tags) if tags else None,
                page=page,
                per_page=per_page,
            )
        )

        # Display results
        table = Table(title="Search Results")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Version")
        table.add_column("Author")
        table.add_column("Description")

        for artifact in results["artifacts"]:
            table.add_row(
                artifact["name"],
                artifact["type"],
                artifact["version"],
                artifact["author"],
                (
                    artifact["description"][:50] + "..."
                    if len(artifact["description"]) > 50
                    else artifact["description"]
                ),
            )

        console.print(table)
        console.print(
            f"\nShowing {len(results['artifacts'])} of {results['total']} results"
        )
        console.print(f"Page {page} of {results['total_pages']}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@hub.command()
@click.argument("artifact_id")
def info(artifact_id: str) -> None:
    """Get detailed information about an artifact.

    ARTIFACT_ID is the ID of the artifact to inspect.
    """
    try:
        # Initialize components
        storage = LocalStorageBackend()
        security = SecurityManager(SecurityConfig())
        marketplace = MarketplaceManager(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Run async info in event loop
        loop = asyncio.get_event_loop()
        details = loop.run_until_complete(marketplace.get_artifact(artifact_id))

        # Display details
        console.print("\n[bold]Artifact Details[/bold]")
        console.print(f"ID: {artifact_id}")
        console.print(f"Name: {details['name']}")
        console.print(f"Type: {details['type']}")
        console.print(f"Version: {details['version']}")
        console.print(f"Author: {details['author']}")
        console.print(f"Description: {details['description']}")
        console.print(f"Tags: {', '.join(details['tags'])}")
        console.print(f"Visibility: {details['visibility']}")
        console.print(f"Created: {details['created_at']}")
        console.print(f"Updated: {details['updated_at']}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@hub.command()
@click.argument("artifact_id")
def delete(artifact_id: str) -> None:
    """Delete an artifact from the Hub.

    ARTIFACT_ID is the ID of the artifact to delete.
    """
    try:
        # Initialize components
        storage = LocalStorageBackend()
        security = SecurityManager(SecurityConfig())
        marketplace = MarketplaceManager(
            config=MarketplaceConfig(),
            storage=storage,
            security=security,
        )

        # Run async delete in event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(marketplace.delete_artifact(artifact_id))
        console.print(f"[green]Successfully deleted artifact:[/green] {artifact_id}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


@hub.command()
def list() -> None:
    """List local artifacts."""
    try:
        # Initialize storage
        storage = LocalStorageBackend()

        # Run async list in event loop
        loop = asyncio.get_event_loop()
        artifacts = loop.run_until_complete(storage.list())

        # Display artifacts
        table = Table(title="Local Artifacts")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Version")

        for artifact in artifacts:
            table.add_row(
                str(artifact.id),
                artifact.name,
                artifact.artifact_type,
                artifact.version,
            )

        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort() from e


"""Hub commands for the Pepperpy CLI.

This module provides commands for:
- Publishing artifacts to the Hub
- Installing artifacts from the marketplace
- Managing local artifacts
- Searching the marketplace
"""


# Configure rich console
console = Console()


@click.group()
def hub() -> None:
    """Manage Pepperpy Hub artifacts and marketplace."""
    pass


@hub.command()
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
        raise click.Abort() from e


@hub.command()
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
        raise click.Abort() from e


@hub.command()
@click.option("--query", help="Search query")
@click.option("--type", "artifact_type", help="Filter by artifact type")
@click.option("--tags", help="Filter by tags (comma-separated)")
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
        raise click.Abort() from e


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
        raise click.Abort() from e


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
        raise click.Abort() from e


@hub.command()
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
        raise click.Abort() from e
