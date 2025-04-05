"""
Storage Provider Interface.

This module defines the core interfaces for storage providers in PepperPy.
Storage providers enable persistent data storage with different backends like
SQLite, PostgreSQL, or cloud storage services.
"""

from datetime import datetime
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.errors import PepperpyError


class StorageError(PepperpyError):
    """Base error for storage-related exceptions."""

    def __init__(
        self,
        message: str,
        container: str | None = None,
        object_id: str | None = None,
        operation: str | None = None,
        *args,
        **kwargs,
    ):
        """Initialize storage error.

        Args:
            message: Error message
            container: Optional container/collection name
            object_id: Optional object identifier
            operation: Operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.container = container
        self.object_id = object_id
        self.operation = operation


class ObjectNotFoundError(StorageError):
    """Error raised when an object is not found in storage."""

    def __init__(
        self,
        object_id: str,
        container: str | None = None,
        *args,
        **kwargs,
    ):
        """Initialize object not found error.

        Args:
            object_id: Object identifier
            container: Optional container/collection name
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        message = f"Object not found: {object_id}"
        if container:
            message += f" in container {container}"
        super().__init__(
            message, container=container, object_id=object_id, *args, **kwargs
        )


class ContainerNotFoundError(StorageError):
    """Error raised when a container is not found in storage."""

    def __init__(
        self,
        container: str,
        *args,
        **kwargs,
    ):
        """Initialize container not found error.

        Args:
            container: Container/collection name
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        message = f"Container not found: {container}"
        super().__init__(message, container=container, *args, **kwargs)


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


T = TypeVar("T", bound=StorageObject)


class StorageContainer(Generic[T]):
    """A container for storage objects.

    A container is a collection of related objects, similar to a table in a
    database or a collection in MongoDB. Each container has a name and a
    schema that describes the structure of objects it can store.
    """

    def __init__(
        self,
        name: str,
        object_type: type[T],
        description: str | None = None,
    ):
        """Initialize storage container.

        Args:
            name: Container name
            object_type: Type of objects in this container
            description: Optional description
        """
        self.name = name
        self.object_type = object_type
        self.description = (
            description or f"Container for {object_type.__name__} objects"
        )


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


class StorageResult(BaseModel, Generic[T]):
    """Result of a storage query operation.

    This model provides a standardized way to return query results, including
    the matched objects and pagination information.
    """

    items: list[T]
    total: int
    page: int = 1
    pages: int | None = None
    has_more: bool = False


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

    async def query(self, container_name: str, query: StorageQuery) -> StorageResult[T]:
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
    ) -> StorageResult[T]:
        """Search objects in the storage backend.

        Args:
            container_name: Container name
            text: Search text
            fields: Fields to search in
            limit: Maximum number of results

        Returns:
            Search result with matched objects
        """
        ...
