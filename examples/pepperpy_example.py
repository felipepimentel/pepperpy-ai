#!/usr/bin/env python
"""
PepperPy Framework Example.

This script demonstrates how to use the PepperPy framework with
various providers including the new SQLite storage provider.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from pepperpy import PepperPy
from pepperpy.storage.base.provider import StorageContainer
from pepperpy.storage.providers.sqlite import SQLiteConfig, SQLiteProvider


class TestObject:
    """Test object for storage."""

    def __init__(self, id: str, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: dict[str, Any] = {}


async def main():
    """Run the example."""
    # Create a data directory
    data_dir = Path("examples/data")
    data_dir.mkdir(exist_ok=True)

    # Create PepperPy instance
    pepperpy = PepperPy()

    # Configure SQLite storage provider
    sqlite_config = SQLiteConfig(
        database_path=str(data_dir / "pepperpy.db"),
        create_if_missing=True,
    )

    # Create SQLite provider
    sqlite_provider = SQLiteProvider(config=sqlite_config)

    # Add storage provider to PepperPy
    pepperpy.with_storage(sqlite_provider)

    # Initialize all providers
    await pepperpy.initialize()

    # Access the storage provider
    storage = pepperpy.storage
    print(f"Storage provider: {storage.name}")
    print(f"Storage type: {storage.type}")

    # Create a container for test objects
    container_name = "test_objects"
    container = StorageContainer(
        name=container_name,
        object_type=TestObject,
        description="Container for test objects",
    )

    # Check if container exists
    if not await storage.container_exists(container_name):
        await storage.create_container(container)
        print(f"Created container: {container_name}")
    else:
        print(f"Container already exists: {container_name}")

    # Store an object
    test_object = TestObject(
        id="test-1",
        name="Test Object",
        description="This is a test object for demonstrating storage",
    )

    stored = await storage.put(container_name, test_object)
    print(f"Stored object: {stored.id}")

    # Get the object
    retrieved = await storage.get(container_name, "test-1")
    print(f"Retrieved object: {retrieved['id']}")
    print(f"  Name: {retrieved['name']}")
    print(f"  Description: {retrieved['description']}")

    # Clean up
    print("Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
