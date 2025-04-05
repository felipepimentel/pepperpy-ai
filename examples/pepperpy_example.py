#!/usr/bin/env python
"""
PepperPy Framework Example.

This script demonstrates how to use the PepperPy framework with
various providers using the proper abstraction layer.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pepperpy import PepperPy
from pepperpy.storage.provider import StorageContainer


class TestObject(BaseModel):
    """Test object for storage."""

    id: str
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


async def main():
    """Run the example."""
    # Create a data directory
    data_dir = Path("examples/data")
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "pepperpy.db"

    # Create PepperPy instance
    pepperpy = PepperPy()

    # Configure storage provider through the framework's API
    # This is the correct way - no direct access to provider classes
    pepperpy.with_storage("sqlite", database_path=str(db_path), create_if_missing=True)

    # Initialize all providers
    await pepperpy.initialize()

    # Access the storage provider through the framework
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
