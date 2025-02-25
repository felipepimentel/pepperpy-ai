"""Base resource system.

This module provides core resource functionality:
- Resource definition
- Resource lifecycle
- Resource tracking
- Resource metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pepperpy.core.errors import ResourceError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variable for resource values
T = TypeVar("T")


class ResourceType(str, Enum):
    """Resource types."""

    MEMORY = "memory"
    FILE = "file"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    CUSTOM = "custom"


class ResourceState(str, Enum):
    """Resource states."""

    CREATED = "created"
    ALLOCATED = "allocated"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CLEANED = "cleaned"


@dataclass
class ResourceMetadata:
    """Resource metadata information."""

    type: ResourceType
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    tags: dict[str, str] = field(default_factory=dict)


class Resource(LifecycleComponent, Generic[T]):
    """Base class for resources."""

    def __init__(
        self,
        id: str,
        type: ResourceType,
        value: T,
        state: ResourceState = ResourceState.CREATED,
    ) -> None:
        """Initialize resource.

        Args:
            id: Resource identifier
            type: Resource type
            value: Resource value
            state: Initial state
        """
        super().__init__(f"resource_{id}")
        self.id = id
        self.type = type
        self.value = value
        self._state = state

    @property
    def state(self) -> ResourceState:
        """Get resource state.

        Returns:
            Resource state
        """
        return self._state

    async def initialize(self) -> None:
        """Initialize resource.

        Raises:
            ResourceError: If initialization fails
        """
        try:
            await super().initialize()
            self._state = ResourceState.INITIALIZING
            await self._initialize_resource()
            self._state = ResourceState.ACTIVE
            logger.info(
                "Resource initialized",
                extra={
                    "id": self.id,
                    "type": self.type,
                },
            )
        except Exception as e:
            self._state = ResourceState.ERROR
            raise ResourceError(f"Failed to initialize resource {self.id}: {e}")

    async def cleanup(self) -> None:
        """Clean up resource.

        Raises:
            ResourceError: If cleanup fails
        """
        try:
            await super().cleanup()
            await self._cleanup_resource()
            self._state = ResourceState.CLEANED
            logger.info(
                "Resource cleaned up",
                extra={
                    "id": self.id,
                    "type": self.type,
                },
            )
        except Exception as e:
            self._state = ResourceState.ERROR
            raise ResourceError(f"Failed to clean up resource {self.id}: {e}")

    async def _initialize_resource(self) -> None:
        """Initialize resource implementation.

        This method should be overridden by subclasses to perform
        resource-specific initialization.

        Raises:
            ResourceError: If initialization fails
        """
        pass

    async def _cleanup_resource(self) -> None:
        """Clean up resource implementation.

        This method should be overridden by subclasses to perform
        resource-specific cleanup.

        Raises:
            ResourceError: If cleanup fails
        """
        pass


class MemoryResource(Resource[T]):
    """Resource for memory-based values."""

    async def _cleanup_resource(self) -> None:
        """Clean up memory resource.

        Raises:
            ResourceError: If cleanup fails
        """
        try:
            # Clear reference
            self.value = None  # type: ignore
        except Exception as e:
            raise ResourceError(f"Failed to clean up memory resource: {e}")


class FileResource(Resource[str]):
    """Resource for file-based values."""

    def __init__(
        self,
        id: str,
        path: str,
        mode: str = "r",
    ) -> None:
        """Initialize resource.

        Args:
            id: Resource identifier
            path: File path
            mode: File mode
        """
        super().__init__(id, ResourceType.FILE, path)
        self.mode = mode
        self._file = None

    async def _initialize_resource(self) -> None:
        """Initialize file resource.

        Raises:
            ResourceError: If initialization fails
        """
        try:
            self._file = open(self.value, self.mode)
        except Exception as e:
            raise ResourceError(f"Failed to open file {self.value}: {e}")

    async def _cleanup_resource(self) -> None:
        """Clean up file resource.

        Raises:
            ResourceError: If cleanup fails
        """
        try:
            if self._file:
                self._file.close()
                self._file = None
        except Exception as e:
            raise ResourceError(f"Failed to close file {self.value}: {e}")


class NetworkResource(Resource[str]):
    """Resource for network-based values."""

    def __init__(
        self,
        id: str,
        url: str,
        timeout: float = 30.0,
    ) -> None:
        """Initialize resource.

        Args:
            id: Resource identifier
            url: Network URL
            timeout: Connection timeout
        """
        super().__init__(id, ResourceType.NETWORK, url)
        self.timeout = timeout
        self._connection = None

    async def _initialize_resource(self) -> None:
        """Initialize network resource.

        Raises:
            ResourceError: If initialization fails
        """
        try:
            # Initialize network connection
            pass
        except Exception as e:
            raise ResourceError(f"Failed to connect to {self.value}: {e}")

    async def _cleanup_resource(self) -> None:
        """Clean up network resource.

        Raises:
            ResourceError: If cleanup fails
        """
        try:
            if self._connection:
                # Close network connection
                self._connection = None
        except Exception as e:
            raise ResourceError(f"Failed to close connection to {self.value}: {e}")


# Export public API
__all__ = [
    "FileResource",
    "MemoryResource",
    "NetworkResource",
    "Resource",
    "ResourceMetadata",
    "ResourceState",
    "ResourceType",
]
