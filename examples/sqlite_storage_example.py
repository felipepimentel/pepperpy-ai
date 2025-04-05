#!/usr/bin/env python
"""
SQLite Storage Provider Example.

This script demonstrates how to use the SQLite storage provider in PepperPy.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pepperpy.storage.base.provider import StorageContainer, StorageQuery
from pepperpy.storage.providers.sqlite import SQLiteProvider
from pepperpy.storage.providers.sqlite.provider import SQLiteConfig


class Note(BaseModel):
    """A simple note model for the example."""

    id: str
    title: str
    content: str
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


async def main():
    """Run the example."""
    # Get path for the database
    examples_dir = Path(__file__).parent
    data_dir = examples_dir / "data"
    db_path = data_dir / "notes.db"

    # Create a SQLite configuration
    config = SQLiteConfig(
        database_path=str(db_path),
        create_if_missing=True,
    )

    # Create a SQLite provider
    provider = SQLiteProvider(config)

    try:
        # Connect to the database
        connection = await provider.get_connection()
        print(f"Connected to SQLite database: {config.database_path}")

        # Create a container for notes
        container_name = "notes"
        container = StorageContainer(
            name=container_name,
            object_type=Note,
            description="Container for storing notes",
        )

        # Check if container exists
        if not await provider.container_exists(container_name):
            await provider.create_container(container)
            print(f"Created container: {container_name}")
        else:
            print(f"Container already exists: {container_name}")

        # Create a new note
        note = Note(
            id="note-1",
            title="Welcome to PepperPy",
            content="This is a simple example of using the SQLite storage provider.",
            tags=["example", "storage", "sqlite"],
        )

        # Store the note
        stored_note = await provider.put(container_name, note)
        print(f"Stored note: {stored_note.id}")
        print(f"  Created at: {stored_note.created_at}")
        print(f"  Updated at: {stored_note.updated_at}")

        # Retrieve the note
        retrieved_note = await provider.get(container_name, "note-1")
        print(f"Retrieved note: {retrieved_note['id']}")
        print(f"  Title: {retrieved_note['title']}")
        print(f"  Content: {retrieved_note['content']}")
        print(f"  Tags: {retrieved_note['tags']}")

        # Update the note
        updated_note = Note(
            id="note-1",
            title="Updated: Welcome to PepperPy",
            content="This note has been updated.",
            tags=["example", "storage", "sqlite", "updated"],
            created_at=retrieved_note["created_at"],
        )

        await provider.put(container_name, updated_note)
        print("Note updated")

        # Create more notes for query example
        for i in range(2, 6):
            note = Note(
                id=f"note-{i}",
                title=f"Note {i}",
                content=f"This is note {i}.",
                tags=["example", f"tag-{i}"],
            )
            await provider.put(container_name, note)
            print(f"Created note: {note.id}")

        # Query notes
        query = StorageQuery(
            limit=10,
        )
        result = await provider.query(container_name, query)
        print(f"Found {result.total} notes:")
        for item in result.items:
            print(f"  {item['id']}: {item['title']}")

        # Search notes
        search_result = await provider.search(container_name, "note-1")
        print(f"Search results for 'note-1': {len(search_result.items)} notes found")
        for item in search_result.items:
            print(f"  {item['id']}: {item['title']}")

        # Count notes
        count = await provider.count(container_name)
        print(f"Total notes: {count}")

        # Uncomment to delete the note
        # await provider.delete(container_name, "note-1")
        # print("Note deleted")

        # Uncomment to delete the container
        # await provider.delete_container(container_name)
        # print(f"Container deleted: {container_name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure to disconnect
        if provider._connection and provider._connection.is_connected:
            await provider._connection.disconnect()
            print("Disconnected from database")


if __name__ == "__main__":
    # Make sure the data directory exists
    examples_dir = Path(__file__).parent
    data_dir = examples_dir / "data"
    data_dir.mkdir(exist_ok=True)

    # Run the example
    asyncio.run(main())
