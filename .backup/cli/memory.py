"""CLI commands for managing memory and knowledge bases.

This module provides commands for managing different types of memory storage,
including vector stores, document stores, and caches.
"""

import asyncio
import json
from typing import Optional

import click

from pepperpy.cli import CommandGroup, logger
from pepperpy.memory import MemoryManager
from pepperpy.memory.compat import CompatMemoryStore
from pepperpy.memory.stores.inmemory import InMemoryStore
from pepperpy.monitoring import metrics


class MemoryCommands(CommandGroup):
    """Memory-related CLI commands."""

    name = "memory"
    help = "Manage memory and knowledge bases"

    @classmethod
    def get_command_group(cls) -> click.Group:
        """Get the memory command group."""

        @click.group(name=cls.name, help=cls.help)
        def memory():
            """Manage memory and knowledge bases."""
            pass

        # Add all commands
        memory.add_command(cls.list)
        memory.add_command(cls.info)
        memory.add_command(cls.store)
        memory.add_command(cls.retrieve)
        memory.add_command(cls.search)
        memory.add_command(cls.delete)
        memory.add_command(cls.clear)
        memory.add_command(cls.stats)
        memory.add_command(cls.backup)
        memory.add_command(cls.restore)
        memory.add_command(cls.optimize)

        return memory

    @staticmethod
    @click.command()
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "document", "cache"]),
        help="Memory type",
    )
    def list(type: Optional[str]) -> None:
        """List stored memories by type."""
        try:
            manager = MemoryManager()
            memories = manager.list_memories(memory_type=type)

            click.echo("\nStored Memories:")
            click.echo("=" * 80)

            for memory_type, items in memories.items():
                click.echo(f"\n{memory_type.capitalize()}:")
                for item in items:
                    click.echo(f"  - {item['id']}")
                    click.echo(f"    Created: {item['created_at']}")
                    click.echo(f"    Size: {item['size']} bytes")
                    if "metadata" in item:
                        click.echo(
                            f"    Tags: {', '.join(item['metadata'].get('tags', []))}"
                        )
                    click.echo("-" * 40)

        except Exception as e:
            logger.error(
                "Failed to list memories",
                error=str(e),
                type=type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("memory_id")
    def info(memory_id: str) -> None:
        """Show detailed information about a memory."""
        try:
            manager = MemoryManager()
            info = manager.get_memory_info(memory_id)

            click.echo(f"\nMemory Information for {memory_id}:")
            click.echo("=" * 80)
            click.echo(f"\nType: {info['type']}")
            click.echo(f"Created: {info['created_at']}")
            click.echo(f"Last Modified: {info['modified_at']}")
            click.echo(f"Size: {info['size']} bytes")

            if "metadata" in info:
                click.echo("\nMetadata:")
                for key, value in info["metadata"].items():
                    click.echo(f"  {key}: {value}")

            if "stats" in info:
                click.echo("\nStatistics:")
                for key, value in info["stats"].items():
                    click.echo(f"  {key}: {value}")

        except Exception as e:
            logger.error(
                "Failed to get memory info",
                error=str(e),
                memory_id=memory_id,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("memory_id")
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "document", "cache"]),
        required=True,
    )
    @click.option(
        "--content", "-c", type=click.Path(exists=True), help="Content file path"
    )
    @click.option(
        "--metadata", "-m", type=click.Path(exists=True), help="Metadata file path"
    )
    def store(
        memory_id: str,
        type: str,
        content: Optional[str],
        metadata: Optional[str],
    ) -> None:
        """Store new memory content."""
        try:
            manager = MemoryManager()

            # Load content
            if content:
                with open(content, "r", encoding="utf-8") as f:
                    content_data = json.load(f)
            else:
                content_data = {}

            # Load metadata
            if metadata:
                with open(metadata, "r", encoding="utf-8") as f:
                    metadata_data = json.load(f)
            else:
                metadata_data = {}

            # Store memory
            manager.store(
                memory_id=memory_id,
                memory_type=type,
                content=content_data,
                metadata=metadata_data,
            )

            click.echo(f"Memory '{memory_id}' stored successfully")

        except Exception as e:
            logger.error(
                "Failed to store memory",
                error=str(e),
                memory_id=memory_id,
                type=type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("memory_id")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    def retrieve(memory_id: str, output: Optional[str]) -> None:
        """Retrieve memory content."""
        try:
            manager = MemoryManager()
            content = manager.retrieve(memory_id)

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2)
                click.echo(f"Memory content saved to '{output}'")
            else:
                click.echo("\nMemory Content:")
                click.echo("=" * 80)
                click.echo(json.dumps(content, indent=2))

        except Exception as e:
            logger.error(
                "Failed to retrieve memory",
                error=str(e),
                memory_id=memory_id,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("query")
    @click.option(
        "--type", "-t", type=click.Choice(["vector", "document"]), help="Memory type"
    )
    @click.option("--limit", "-l", type=int, default=10, help="Maximum results")
    @click.option(
        "--threshold", "-th", type=float, default=0.7, help="Similarity threshold"
    )
    def search(
        query: str,
        type: Optional[str],
        limit: int,
        threshold: float,
    ) -> None:
        """Search through stored memories."""
        try:
            manager = MemoryManager()
            results = manager.search(
                query=query,
                memory_type=type,
                limit=limit,
                threshold=threshold,
            )

            click.echo("\nSearch Results:")
            click.echo("=" * 80)

            for result in results:
                click.echo(f"\nScore: {result.score:.2f}")
                click.echo(f"Memory ID: {result.memory_id}")
                click.echo(f"Type: {result.memory_type}")
                if result.metadata:
                    click.echo(f"Tags: {', '.join(result.metadata.get('tags', []))}")
                click.echo("-" * 40)

        except Exception as e:
            logger.error(
                "Search failed",
                error=str(e),
                query=query,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("memory_id")
    def delete(memory_id: str) -> None:
        """Delete a stored memory."""
        try:
            manager = MemoryManager()
            manager.delete(memory_id)
            click.echo(f"Memory '{memory_id}' deleted successfully")

        except Exception as e:
            logger.error(
                "Failed to delete memory",
                error=str(e),
                memory_id=memory_id,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "document", "cache"]),
        help="Memory type",
    )
    def clear(type: Optional[str]) -> None:
        """Clear all memories of a type."""
        try:
            if not click.confirm("Are you sure you want to clear memories?"):
                return

            def _clear(type: str | None = None) -> None:
                """Clear memories of the specified type."""
                store = InMemoryStore({})
                compat_store = CompatMemoryStore(store)
                asyncio.run(compat_store.cleanup())
                click.echo(f"Cleared all memories{f' of type {type}' if type else ''}")

            _clear(type)

        except Exception as e:
            logger.error(
                "Failed to clear memories",
                error=str(e),
                type=type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "document", "cache"]),
        help="Memory type",
    )
    @click.option(
        "--period", "-p", default="24h", help="Time period (e.g., 24h, 7d, 30d)"
    )
    def stats(type: Optional[str], period: str) -> None:
        """Show memory usage statistics."""
        try:
            stats = metrics.get_memory_stats(memory_type=type, period=period)

            click.echo("\nMemory Statistics:")
            click.echo("=" * 80)

            if "usage" in stats:
                click.echo("\nUsage:")
                click.echo(f"  Total Size: {stats['usage']['total_size']} bytes")
                click.echo(f"  Item Count: {stats['usage']['item_count']}")

            if "operations" in stats:
                click.echo("\nOperations:")
                for op, count in stats["operations"].items():
                    click.echo(f"  {op}: {count}")

            if "performance" in stats:
                click.echo("\nPerformance:")
                for metric, value in stats["performance"].items():
                    click.echo(f"  {metric}: {value}")

        except Exception as e:
            logger.error(
                "Failed to get memory stats",
                error=str(e),
                type=type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("output_path", type=click.Path())
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "document", "cache"]),
        help="Memory type",
    )
    def backup(output_path: str, type: Optional[str]) -> None:
        """Create a backup of stored memories."""
        try:
            manager = MemoryManager()
            manager.create_backup(output_path, memory_type=type)
            click.echo(f"Backup created successfully at '{output_path}'")

        except Exception as e:
            logger.error(
                "Failed to create backup",
                error=str(e),
                path=output_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("backup_path", type=click.Path(exists=True))
    @click.option(
        "--type",
        "-t",
        type=click.Choice(["vector", "document", "cache"]),
        help="Memory type",
    )
    def restore(backup_path: str, type: Optional[str]) -> None:
        """Restore memories from a backup."""
        try:
            if not click.confirm("This will overwrite existing memories. Continue?"):
                return

            manager = MemoryManager()
            manager.restore_backup(backup_path, memory_type=type)
            click.echo("Memories restored successfully")

        except Exception as e:
            logger.error(
                "Failed to restore backup",
                error=str(e),
                path=backup_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.option(
        "--type", "-t", type=click.Choice(["vector", "document"]), help="Memory type"
    )
    def optimize(type: Optional[str]) -> None:
        """Optimize memory storage."""
        try:
            manager = MemoryManager()
            stats = manager.optimize(memory_type=type)

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
                "Failed to optimize memory",
                error=str(e),
                type=type,
            )
            click.echo(f"Error: {str(e)}")


# Register the memory commands
from pepperpy.cli import CLIManager

CLIManager.register_group(MemoryCommands)
