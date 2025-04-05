"""
Storage Provider Interface.

This module defines the core interfaces for storage providers in PepperPy.
Storage providers enable persistent data storage with different backends like
SQLite, PostgreSQL, or cloud storage services.
"""

import importlib
import os
from datetime import datetime
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.errors import PepperpyError

# Type variable for generic object types
T = TypeVar("T")


class StorageError(PepperpyError):
    """Base error class for storage operations."""

    def __init__(
        self,
        message: str,
        container: str | None = None,
        object_id: str | None = None,
        operation: str | None = None,
        *args,
        **kwargs,
    ):
        """Initialize StorageError.

        Args:
            message: Error message
            container: Optional container name where the error occurred
            object_id: Optional object ID where the error occurred
            operation: Optional operation that caused the error
        """
        self.container = container
        self.object_id = object_id
        self.operation = operation

        # Enhance message with context
        context = []
        if container:
            context.append(f"container='{container}'")
        if object_id:
            context.append(f"id='{object_id}'")
        if operation:
            context.append(f"op='{operation}'")

        if context:
            message = f"{message} ({', '.join(context)})"

        super().__init__(message, *args, **kwargs)


class ObjectNotFoundError(StorageError):
    """Error raised when an object is not found in storage."""

    def __init__(
        self,
        object_id: str,
        container: str | None = None,
        *args,
        **kwargs,
    ):
        """Initialize ObjectNotFoundError.

        Args:
            object_id: ID of the object that was not found
            container: Optional container name
        """
        self.object_id = object_id
        self.container = container

        container_msg = f" in container '{container}'" if container else ""
        message = f"Object with id '{object_id}' not found{container_msg}"
        super().__init__(
            message,
            container=container,
            object_id=object_id,
            operation="get",
            *args,
            **kwargs,
        )


class ContainerNotFoundError(StorageError):
    """Error raised when a container is not found in storage."""

    def __init__(
        self,
        container: str,
        *args,
        **kwargs,
    ):
        """Initialize ContainerNotFoundError.

        Args:
            container: Name of the container that was not found
        """
        self.container = container

        message = f"Container '{container}' not found"
        super().__init__(
            message,
            container=container,
            operation="access",
            *args,
            **kwargs,
        )


class StorageConfig(BaseModel):
    """Configuration for a storage provider.

    This model contains common configuration options for storage providers.
    Specific providers may extend this with additional options.
    """

    connection_string: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    ssl: bool = False
    connection_timeout: int = 30
    pool_size: int = 5
    max_overflow: int = 10
    max_retries: int = 3

    class Config:
        """Allow extra fields for provider-specific options."""

        extra = "allow"


class StorageObject(Protocol):
    """Protocol for objects that can be stored in PepperPy storage.

    This protocol establishes a common interface for storable objects, including
    required fields like id, metadata, and created/updated timestamps.

    All storable objects must have:
    - An id field (required, string)
    - A created_at timestamp (automatically set on creation)
    - An updated_at timestamp (automatically updated on changes)
    - A metadata field for arbitrary key-value data
    """

    id: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]


class StorageContainer(Generic[T]):
    """Container definition for storage.

    A container represents a logical grouping of objects of the same type,
    similar to a table or collection. This class stores the metadata about
    the container, including its name, object type, and description.
    """

    def __init__(
        self,
        name: str,
        object_type: type[T],
        description: str | None = None,
    ):
        """Initialize a storage container.

        Args:
            name: Container name (must be unique within a storage provider)
            object_type: Type of objects stored in this container
            description: Optional description of the container
        """
        self.name = name
        self.object_type = object_type
        self.description = description


class StorageQuery(BaseModel):
    """Query parameters for retrieving objects from storage.

    This model provides a standardized way to express filtering, sorting,
    pagination, and other query operations across different storage backends.
    """

    filter: dict[str, Any] = Field(default_factory=dict)
    sort: list[str] = Field(default_factory=list)
    limit: int | None = None
    offset: int | None = None
    fields: list[str] = Field(default_factory=list)

    # Full-text search
    search: str | None = None
    search_fields: list[str] = Field(default_factory=list)


class StorageResult(BaseModel):
    """Result of a storage query operation.

    This model provides a standardized way to return query results, including
    the matched objects and pagination information.
    """

    items: list[Any]
    total: int
    page: int = 1
    pages: int | None = None
    has_more: bool = False

    model_config = {
        "arbitrary_types_allowed": True,
    }


class StorageConnection(Protocol):
    """Protocol for storage connections.

    This protocol defines the methods that a storage connection must implement.
    A connection represents an active session with a storage backend.
    """

    @property
    def is_connected(self) -> bool:
        """Check if the connection is active."""
        ...

    async def connect(self) -> None:
        """Establish a connection to the storage backend."""
        ...

    async def disconnect(self) -> None:
        """Close the connection to the storage backend."""
        ...

    async def ping(self) -> bool:
        """Check connectivity to the storage backend.

        Returns:
            True if connection is healthy, False otherwise
        """
        ...


class StorageProvider(Protocol):
    """Protocol for storage providers.

    This protocol defines the methods that a storage provider must implement.
    Storage providers handle the connection to a specific storage backend and
    provide operations to store, retrieve, update, and delete objects.
    """

    @property
    def name(self) -> str:
        """Get the provider name."""
        ...

    @property
    def type(self) -> str:
        """Get the provider type."""
        ...

    @property
    def config(self) -> StorageConfig:
        """Get the provider configuration."""
        ...

    async def get_connection(self) -> StorageConnection:
        """Get a connection to the storage backend.

        Returns:
            Connection to the storage backend
        """
        ...

    async def create_container(self, container: StorageContainer[T]) -> None:
        """Create a container (table/collection) in the storage backend.

        Args:
            container: Container definition
        """
        ...

    async def delete_container(self, container_name: str) -> None:
        """Delete a container from the storage backend.

        Args:
            container_name: Container name
        """
        ...

    async def list_containers(self) -> list[str]:
        """List containers in the storage backend.

        Returns:
            List of container names
        """
        ...

    async def container_exists(self, container_name: str) -> bool:
        """Check if a container exists in the storage backend.

        Args:
            container_name: Container name

        Returns:
            True if container exists, False otherwise
        """
        ...

    async def put(self, container_name: str, object: T) -> T:
        """Store an object in the storage backend.

        If an object with the same ID already exists, it will be updated.
        Otherwise, a new object will be created.

        Args:
            container_name: Container name
            object: Object to store

        Returns:
            Stored object (may include auto-generated fields)
        """
        ...

    async def get(self, container_name: str, object_id: str) -> T:
        """Retrieve an object from the storage backend.

        Args:
            container_name: Container name
            object_id: Object ID

        Returns:
            Retrieved object

        Raises:
            ObjectNotFoundError: If object not found
        """
        ...

    async def delete(self, container_name: str, object_id: str) -> None:
        """Delete an object from the storage backend.

        Args:
            container_name: Container name
            object_id: Object ID

        Raises:
            ObjectNotFoundError: If object not found
        """
        ...

    async def query(self, container_name: str, query: StorageQuery) -> StorageResult:
        """Query objects from the storage backend.

        Args:
            container_name: Container name
            query: Query parameters

        Returns:
            Query result with matched objects
        """
        ...

    async def count(
        self, container_name: str, query: StorageQuery | None = None
    ) -> int:
        """Count objects in the storage backend.

        Args:
            container_name: Container name
            query: Optional query parameters

        Returns:
            Number of objects that match the query
        """
        ...

    async def search(
        self,
        container_name: str,
        text: str,
        fields: list[str] | None = None,
        limit: int = 10,
    ) -> StorageResult:
        """Search objects in the storage backend.

        Args:
            container_name: Container name
            text: Search text
            fields: Fields to search in (None means all text fields)
            limit: Maximum number of results to return

        Returns:
            Search results with matched objects
        """
        ...


def create_provider(
    provider_type: str = "sqlite",
    **config: Any,
) -> StorageProvider:
    """Create a storage provider instance.

    This factory function creates a storage provider instance based on the
    specified provider type. It dynamically imports the appropriate provider
    module and class.

    Args:
        provider_type: Provider type, such as "sqlite" or "postgres"
        **config: Provider-specific configuration options

    Returns:
        Storage provider instance

    Raises:
        ImportError: If provider module not found
        ValueError: If provider type is invalid
    """
    # Default to sqlite if not specified
    provider_type = provider_type or os.environ.get(
        "PEPPERPY_STORAGE_PROVIDER", "sqlite"
    )

    try:
        # Dynamically import provider module
        module_path = (
            f".providers.{provider_type}.provider"
            if provider_type != "basic"
            else ".basic"
        )
        provider_module = importlib.import_module(
            module_path, package="pepperpy.storage"
        )

        # Get provider class
        class_name = f"{provider_type.capitalize()}StorageProvider"
        provider_class = getattr(provider_module, class_name)

        # Create instance
        return provider_class(**config)
    except ImportError as e:
        # Check if the provider exists in plugins
        try:
            from pepperpy.plugin import create_provider_instance

            return create_provider_instance("storage", provider_type, **config)
        except Exception:
            # If not found in plugins, re-raise original error
            raise ImportError(
                f"Storage provider '{provider_type}' not found: {e}"
            ) from e
    except AttributeError as e:
        raise ValueError(f"Invalid storage provider '{provider_type}': {e}") from e
