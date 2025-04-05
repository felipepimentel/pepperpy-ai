"""
Storage Provider Tests.

Tests for the storage provider implementations without direct coupling.
"""

import os
import tempfile
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import pytest
from pydantic import BaseModel, Field

from pepperpy import PepperPy
from pepperpy.storage.provider import StorageContainer, StorageQuery


class TestObject(BaseModel):
    """Test object for storage tests."""

    id: str
    name: str
    description: str
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


@pytest.fixture
async def db_path() -> str:
    """Create a temporary database path."""
    # Use a temporary file for the database
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, "pepperpy_test.db")

    # Remove the test database if it exists
    if os.path.exists(db_path):
        os.unlink(db_path)

    return db_path


@pytest.fixture
async def pepperpy_instance(db_path: str) -> AsyncGenerator[PepperPy, None]:
    """Create a PepperPy instance with SQLite storage."""
    # Create PepperPy with SQLite storage provider
    pepperpy = PepperPy()

    # Configure with SQLite provider through the framework
    pepperpy.with_storage(
        "sqlite",
        database_path=db_path,
        create_if_missing=True,
        journal_mode="MEMORY",  # Use in-memory journal for tests
        synchronous="OFF",
    )  # Disable synchronous mode for tests

    # Initialize providers
    await pepperpy.initialize()

    yield pepperpy

    # Clean up
    await pepperpy.storage._connection.disconnect()  # type: ignore

    # Delete the test database
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def test_container(pepperpy_instance: PepperPy) -> AsyncGenerator[str, None]:
    """Create a test container."""
    provider = pepperpy_instance.storage

    container_name = "test_objects"
    container = StorageContainer(
        name=container_name,
        object_type=TestObject,
        description="Test objects container",
    )

    await provider.create_container(container)

    yield container_name

    # Clean up
    await provider.delete_container(container_name)


@pytest.mark.asyncio
async def test_provider_initialization(pepperpy_instance: PepperPy) -> None:
    """Test provider initialization."""
    provider = pepperpy_instance.storage

    assert provider.name == "sqlite"
    assert provider.type == "storage"
    assert hasattr(provider, "config")


@pytest.mark.asyncio
async def test_container_operations(pepperpy_instance: PepperPy) -> None:
    """Test container operations."""
    provider = pepperpy_instance.storage

    # Create container
    container_name = "test_container_ops"
    container = StorageContainer(
        name=container_name,
        object_type=TestObject,
        description="Test container operations",
    )

    await provider.create_container(container)

    # Check if container exists
    exists = await provider.container_exists(container_name)
    assert exists is True

    # List containers
    containers = await provider.list_containers()
    assert container_name in containers

    # Delete container
    await provider.delete_container(container_name)

    # Check if container was deleted
    exists = await provider.container_exists(container_name)
    assert exists is False


@pytest.mark.asyncio
async def test_object_crud(pepperpy_instance: PepperPy, test_container: str) -> None:
    """Test object CRUD operations."""
    provider = pepperpy_instance.storage

    # Create test object
    test_obj = TestObject(
        id="test1",
        name="Test Object",
        description="A test object for CRUD operations",
        tags=["test", "crud"],
    )

    # Store object
    stored_obj = await provider.put(test_container, test_obj)

    # Verify timestamps were set
    assert stored_obj.created_at is not None
    assert stored_obj.updated_at is not None

    # Get object
    retrieved_obj = await provider.get(test_container, "test1")

    # Verify object data
    assert retrieved_obj["id"] == test_obj.id
    assert retrieved_obj["name"] == test_obj.name
    assert retrieved_obj["description"] == test_obj.description
    assert retrieved_obj["tags"] == test_obj.tags

    # Update object
    updated_obj = TestObject(
        id="test1",
        name="Updated Test Object",
        description="An updated test object",
        tags=["test", "crud", "updated"],
        created_at=retrieved_obj["created_at"],
    )

    await provider.put(test_container, updated_obj)

    # Get updated object
    retrieved_updated = await provider.get(test_container, "test1")

    # Verify updated data
    assert retrieved_updated["name"] == updated_obj.name
    assert retrieved_updated["tags"] == updated_obj.tags

    # Delete object
    await provider.delete(test_container, "test1")

    # Verify object was deleted
    with pytest.raises(Exception):
        await provider.get(test_container, "test1")


@pytest.mark.asyncio
async def test_query_and_search(
    pepperpy_instance: PepperPy, test_container: str
) -> None:
    """Test query and search operations."""
    provider = pepperpy_instance.storage

    # Create test objects
    test_objects = [
        TestObject(
            id=f"test{i}",
            name=f"Test Object {i}",
            description=f"Test object {i} for query testing",
            tags=["test", "query", f"tag{i}"],
        )
        for i in range(1, 6)
    ]

    # Store objects
    for obj in test_objects:
        await provider.put(test_container, obj)

    # Query all objects
    query_result = await provider.query(test_container, StorageQuery(limit=10))

    # Verify query results
    assert query_result.total == 5
    assert len(query_result.items) == 5

    # Query with filter
    filter_query = StorageQuery(filter={"id": "test1"}, limit=10)

    filter_result = await provider.query(test_container, filter_query)

    # Verify filtered results
    assert filter_result.total == 1
    assert len(filter_result.items) == 1
    assert filter_result.items[0]["id"] == "test1"

    # Test pagination
    page_query = StorageQuery(limit=2, offset=0)
    page1_result = await provider.query(test_container, page_query)

    # Verify pagination
    assert page1_result.total == 5  # Total count should be all objects
    assert len(page1_result.items) == 2  # But only 2 returned
    assert page1_result.has_more is True

    # Test search
    search_result = await provider.search(test_container, "test1")

    # Verify search results
    assert len(search_result.items) == 1
    assert search_result.items[0]["id"] == "test1"

    # Test count
    count = await provider.count(test_container)
    assert count == 5
