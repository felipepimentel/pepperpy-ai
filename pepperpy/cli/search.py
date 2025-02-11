"""CLI commands for managing search and indexing capabilities.

This module provides commands for managing vector stores, search indexes,
and semantic search functionality.
"""

import json
from typing import Optional

import click

from pepperpy.cli import CommandGroup, logger
from pepperpy.monitoring import metrics
from pepperpy.search import SearchManager


class SearchCommands(CommandGroup):
    """Search-related CLI commands."""

    name = "search"
    help = "Manage search and indexing capabilities"

    @classmethod
    def get_command_group(cls) -> click.Group:
        """Get the search command group."""

        @click.group(name=cls.name, help=cls.help)
        def search():
            """Manage search and indexing capabilities."""
            pass

        # Add all commands
        search.add_command(cls.list)
        search.add_command(cls.info)
        search.add_command(cls.create)
        search.add_command(cls.delete)
        search.add_command(cls.query)
        search.add_command(cls.index)
        search.add_command(cls.stats)
        search.add_command(cls.optimize)
        search.add_command(cls.backup)
        search.add_command(cls.restore)

        return search

    @staticmethod
    @click.command()
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "text", "hybrid"]),
        help="Index type",
    )
    def list(type: Optional[str]) -> None:
        """List available search indexes."""
        try:
            manager = SearchManager()
            indexes = manager.list_indexes(index_type=type)

            click.echo("\nAvailable Indexes:")
            click.echo("=" * 80)

            for index_type, items in indexes.items():
                click.echo(f"\n{index_type.capitalize()}:")
                for item in items:
                    click.echo(f"  - {item['name']}")
                    click.echo(f"    Documents: {item['doc_count']}")
                    click.echo(f"    Size: {item['size']} bytes")
                    if "metadata" in item:
                        click.echo(
                            f"    Tags: {', '.join(item['metadata'].get('tags', []))}"
                        )
                    click.echo("-" * 40)

        except Exception as e:
            logger.error(
                "Failed to list indexes",
                error=str(e),
                type=type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    def info(index_name: str) -> None:
        """Show detailed information about an index."""
        try:
            manager = SearchManager()
            info = manager.get_index_info(index_name)

            click.echo(f"\nIndex Information for {index_name}:")
            click.echo("=" * 80)
            click.echo(f"\nType: {info['type']}")
            click.echo(f"Created: {info['created_at']}")
            click.echo(f"Last Updated: {info['updated_at']}")
            click.echo(f"Document Count: {info['doc_count']}")
            click.echo(f"Size: {info['size']} bytes")

            if "config" in info:
                click.echo("\nConfiguration:")
                for key, value in info["config"].items():
                    click.echo(f"  {key}: {value}")

            if "stats" in info:
                click.echo("\nStatistics:")
                for key, value in info["stats"].items():
                    click.echo(f"  {key}: {value}")

        except Exception as e:
            logger.error(
                "Failed to get index info",
                error=str(e),
                index=index_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    @click.option(
        "--type", "-t", type=click.Choice(["vector", "text", "hybrid"]), required=True
    )
    @click.option(
        "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
    )
    def create(
        index_name: str,
        type: str,
        config: Optional[str],
    ) -> None:
        """Create a new search index."""
        try:
            manager = SearchManager()

            # Load configuration if provided
            if config:
                with open(config, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            else:
                config_data = {}

            # Create index
            manager.create_index(
                name=index_name,
                index_type=type,
                config=config_data,
            )

            click.echo(f"Index '{index_name}' created successfully")

        except Exception as e:
            logger.error(
                "Failed to create index",
                error=str(e),
                name=index_name,
                type=type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    def delete(index_name: str) -> None:
        """Delete a search index."""
        try:
            if not click.confirm(
                f"Are you sure you want to delete index '{index_name}'?"
            ):
                return

            manager = SearchManager()
            manager.delete_index(index_name)
            click.echo(f"Index '{index_name}' deleted successfully")

        except Exception as e:
            logger.error(
                "Failed to delete index",
                error=str(e),
                index=index_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    @click.argument("query")
    @click.option("--limit", "-l", type=int, default=10, help="Maximum results")
    @click.option(
        "--threshold", "-th", type=float, default=0.7, help="Similarity threshold"
    )
    @click.option("--filter", "-f", multiple=True, help="Filter results (field:value)")
    def query(
        index_name: str,
        query: str,
        limit: int,
        threshold: float,
        filter: tuple[str, ...],
    ) -> None:
        """Search through an index."""
        try:
            # Parse filters
            filters = {}
            for f in filter:
                field, value = f.split(":", 1)
                filters[field] = value

            manager = SearchManager()
            results = manager.search(
                index_name=index_name,
                query=query,
                limit=limit,
                threshold=threshold,
                filters=filters,
            )

            click.echo("\nSearch Results:")
            click.echo("=" * 80)

            for result in results:
                click.echo(f"\nScore: {result.score:.2f}")
                click.echo(f"Document ID: {result.doc_id}")
                if result.metadata:
                    click.echo("Metadata:")
                    for key, value in result.metadata.items():
                        click.echo(f"  {key}: {value}")
                if result.highlights:
                    click.echo("Highlights:")
                    for highlight in result.highlights:
                        click.echo(f"  ...{highlight}...")
                click.echo("-" * 40)

        except Exception as e:
            logger.error(
                "Search failed",
                error=str(e),
                index=index_name,
                query=query,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    @click.argument("input_path", type=click.Path(exists=True))
    @click.option(
        "--batch-size", "-b", type=int, default=1000, help="Batch size for indexing"
    )
    def index(index_name: str, input_path: str, batch_size: int) -> None:
        """Index documents from a file."""
        try:
            manager = SearchManager()

            # Load documents
            with open(input_path, "r", encoding="utf-8") as f:
                documents = json.load(f)

            # Index documents with progress bar
            with click.progressbar(
                length=len(documents),
                label="Indexing documents",
            ) as bar:

                def progress_callback(indexed: int, total: int) -> None:
                    bar.update(indexed)

                manager.index_documents(
                    index_name=index_name,
                    documents=documents,
                    batch_size=batch_size,
                    progress_callback=progress_callback,
                )

            click.echo(f"Successfully indexed {len(documents)} documents")

        except Exception as e:
            logger.error(
                "Failed to index documents",
                error=str(e),
                index=index_name,
                input=input_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.option("--index", "-i", help="Specific index name")
    @click.option(
        "--period", "-p", default="24h", help="Time period (e.g., 24h, 7d, 30d)"
    )
    def stats(index: Optional[str], period: str) -> None:
        """Show search usage statistics."""
        try:
            stats = metrics.get_search_stats(index_name=index, period=period)

            click.echo("\nSearch Statistics:")
            click.echo("=" * 80)

            if "queries" in stats:
                click.echo("\nQueries:")
                click.echo(f"  Total: {stats['queries']['total']}")
                click.echo(
                    f"  Average Latency: {stats['queries']['avg_latency']:.2f}ms"
                )
                click.echo(
                    f"  Cache Hit Rate: {stats['queries']['cache_hit_rate']:.2f}%"
                )

            if "indexing" in stats:
                click.echo("\nIndexing:")
                click.echo(f"  Documents Indexed: {stats['indexing']['docs_indexed']}")
                click.echo(f"  Index Size: {stats['indexing']['index_size']} bytes")
                click.echo(
                    f"  Average Index Time: {stats['indexing']['avg_index_time']:.2f}ms"
                )

            if "errors" in stats:
                click.echo("\nErrors:")
                for error_type, count in stats["errors"].items():
                    click.echo(f"  {error_type}: {count}")

        except Exception as e:
            logger.error(
                "Failed to get search stats",
                error=str(e),
                index=index,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    def optimize(index_name: str) -> None:
        """Optimize a search index."""
        try:
            manager = SearchManager()
            stats = manager.optimize_index(index_name)

            click.echo("\nOptimization Results:")
            click.echo("=" * 80)
            click.echo(f"Space Saved: {stats['space_saved']} bytes")
            click.echo(f"Time Taken: {stats['time_taken']:.2f}s")
            if "details" in stats:
                click.echo("\nDetails:")
                for key, value in stats["details"].items():
                    click.echo(f"  {key}: {value}")

        except Exception as e:
            logger.error(
                "Failed to optimize index",
                error=str(e),
                index=index_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    @click.argument("output_path", type=click.Path())
    def backup(index_name: str, output_path: str) -> None:
        """Create a backup of a search index."""
        try:
            manager = SearchManager()
            manager.create_backup(index_name, output_path)
            click.echo(f"Backup created successfully at '{output_path}'")

        except Exception as e:
            logger.error(
                "Failed to create backup",
                error=str(e),
                index=index_name,
                path=output_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("index_name")
    @click.argument("backup_path", type=click.Path(exists=True))
    def restore(index_name: str, backup_path: str) -> None:
        """Restore a search index from backup."""
        try:
            if not click.confirm(
                f"This will overwrite index '{index_name}'. Continue?"
            ):
                return

            manager = SearchManager()
            manager.restore_backup(index_name, backup_path)
            click.echo("Index restored successfully")

        except Exception as e:
            logger.error(
                "Failed to restore backup",
                error=str(e),
                index=index_name,
                path=backup_path,
            )
            click.echo(f"Error: {str(e)}")


# Register the search commands
from pepperpy.cli import CLIManager

CLIManager.register_group(SearchCommands)
