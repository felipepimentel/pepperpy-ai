"""Base resource module for the Pepperpy framework.

This module provides core resource functionality including:
- Resource registration and management
- Resource pooling and lifecycle
- Resource cleanup and monitoring
- Resource metrics and validation
"""

import asyncio
import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, Optional, Protocol, TypeVar

from pepperpy.core.base import ComponentBase, Lifecycle
from pepperpy.core.errors import ResourceError, ValidationError
from pepperpy.core.metrics import Counter, Histogram
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.types import (
    Asset,
    AssetMetadata,
    AssetState,
    AssetType,
    Resource,
    ResourceMetadata,
    ResourceState,
    ResourceType,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T", bound="Resource")
P = TypeVar("P", bound="ResourcePool")
M = TypeVar("M", bound="ResourceManager")


class ResourceType(enum.Enum):
    """Resource type enumeration."""

    FILE = "file"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    ASSET = "asset"
    CUSTOM = "custom"


class ResourceState(enum.Enum):
    """Resource state enumeration."""

    CREATED = "created"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass
class ResourceMetadata:
    """Resource metadata class."""

    name: str
    type: ResourceType
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    size: int = 0
    checksum: str | None = None
    content_type: str | None = None
    description: str | None = None
    version: str | None = None
    tags: set[str] = field(default_factory=set)
    dependencies: set[str] = field(default_factory=set)
    custom: dict[str, Any] = field(default_factory=dict)


class Resource(Protocol):
    """Resource protocol.

    This protocol defines the interface for resources.
    """

    @property
    def id(self) -> str:
        """Get resource ID.

        Returns:
            str: Resource ID
        """
        ...

    @property
    def type(self) -> ResourceType:
        """Get resource type.

        Returns:
            ResourceType: Resource type
        """
        ...

    @property
    def state(self) -> ResourceState:
        """Get resource state.

        Returns:
            ResourceState: Resource state
        """
        ...

    @property
    def metadata(self) -> ResourceMetadata:
        """Get resource metadata.

        Returns:
            ResourceMetadata: Resource metadata
        """
        ...

    async def load(self) -> None:
        """Load resource data."""
        ...

    async def save(self) -> None:
        """Save resource data."""
        ...

    async def delete(self) -> None:
        """Delete resource data."""
        ...


class BaseResource(ComponentBase, Resource):
    """Base resource implementation.

    This class provides a base implementation for resources.
    """

    def __init__(
        self,
        id: str,
        type: ResourceType,
        name: str | None = None,
        description: str | None = None,
        version: str | None = None,
        tags: set[str] | None = None,
        dependencies: set[str] | None = None,
        custom: dict[str, Any] | None = None,
    ) -> None:
        """Initialize resource.

        Args:
            id: Resource ID
            type: Resource type
            name: Resource name (defaults to ID)
            description: Resource description
            version: Resource version
            tags: Resource tags
            dependencies: Resource dependencies
            custom: Custom metadata
        """
        super().__init__()
        self._id = id
        self._type = type
        self._state = ResourceState.CREATED
        self._metadata = ResourceMetadata(
            name=name or id,
            type=type,
            description=description,
            version=version,
            tags=tags or set(),
            dependencies=dependencies or set(),
            custom=custom or {},
        )

    @property
    def id(self) -> str:
        """Get resource ID."""
        return self._id

    @property
    def type(self) -> ResourceType:
        """Get resource type."""
        return self._type

    @property
    def state(self) -> ResourceState:
        """Get resource state."""
        return self._state

    @property
    def metadata(self) -> ResourceMetadata:
        """Get resource metadata."""
        return self._metadata

    async def load(self) -> None:
        """Load resource data."""
        try:
            self._state = ResourceState.LOADING
            await self._load()
            self._state = ResourceState.LOADED
            self.metadata.updated_at = datetime.utcnow()
        except Exception as e:
            self._state = ResourceState.FAILED
            logger.error(
                f"Failed to load resource {self.id}: {e}",
                extra={"resource_id": self.id, "type": str(self.type)},
                exc_info=True,
            )
            raise ResourceError(f"Failed to load resource {self.id}: {e}") from e

    async def save(self) -> None:
        """Save resource data."""
        try:
            await self._save()
            self.metadata.updated_at = datetime.utcnow()
        except Exception as e:
            logger.error(
                f"Failed to save resource {self.id}: {e}",
                extra={"resource_id": self.id, "type": str(self.type)},
                exc_info=True,
            )
            raise ResourceError(f"Failed to save resource {self.id}: {e}") from e

    async def delete(self) -> None:
        """Delete resource data."""
        try:
            await self._delete()
            self._state = ResourceState.DELETED
        except Exception as e:
            logger.error(
                f"Failed to delete resource {self.id}: {e}",
                extra={"resource_id": self.id, "type": str(self.type)},
                exc_info=True,
            )
            raise ResourceError(f"Failed to delete resource {self.id}: {e}") from e

    async def _load(self) -> None:
        """Load resource data implementation.

        This method should be overridden by subclasses.
        """
        raise NotImplementedError("_load() must be implemented by subclass")

    async def _save(self) -> None:
        """Save resource data implementation.

        This method should be overridden by subclasses.
        """
        raise NotImplementedError("_save() must be implemented by subclass")

    async def _delete(self) -> None:
        """Delete resource data implementation.

        This method should be overridden by subclasses.
        """
        raise NotImplementedError("_delete() must be implemented by subclass")


class ResourceManager(Lifecycle):
    """Resource manager."""

    _instance: Optional["ResourceManager"] = None

    def __init__(self) -> None:
        """Initialize resource manager."""
        super().__init__()
        self._pools: dict[str, ResourcePool] = {}
        self._state = ComponentState.CREATED

    @classmethod
    def get_instance(cls) -> "ResourceManager":
        """Get resource manager instance.

        Returns:
            Resource manager instance
        """
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize resource manager."""
        try:
            self._state = ComponentState.INITIALIZING
            for pool in self._pools.values():
                await pool.initialize()
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize resource manager: {e}")

    async def cleanup(self) -> None:
        """Clean up resource manager."""
        try:
            self._state = ComponentState.CLEANING
            for pool in self._pools.values():
                await pool.cleanup()
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up resource manager: {e}")

    def add_pool(self, pool: ResourcePool) -> None:
        """Add resource pool.

        Args:
            pool: Resource pool to add

        Raises:
            ValidationError: If pool already exists
        """
        if pool.name in self._pools:
            raise ValidationError(f"Pool already exists: {pool.name}")
        self._pools[pool.name] = pool

    def remove_pool(self, name: str) -> None:
        """Remove resource pool.

        Args:
            name: Pool name

        Raises:
            ValidationError: If pool not found
        """
        if name not in self._pools:
            raise ValidationError(f"Pool not found: {name}")
        del self._pools[name]

    async def acquire_resource(self, pool_name: str, resource_id: str) -> Resource:
        """Acquire resource from pool.

        Args:
            pool_name: Pool name
            resource_id: Resource ID

        Returns:
            Resource instance

        Raises:
            ValidationError: If pool not found
        """
        if pool_name not in self._pools:
            raise ValidationError(f"Pool not found: {pool_name}")
        return await self._pools[pool_name].acquire(resource_id)

    async def release_resource(self, pool_name: str, resource_id: str) -> None:
        """Release resource to pool.

        Args:
            pool_name: Pool name
            resource_id: Resource ID

        Raises:
            ValidationError: If pool not found
        """
        if pool_name not in self._pools:
            raise ValidationError(f"Pool not found: {pool_name}")
        await self._pools[pool_name].release(resource_id)


class ResourcePool(Lifecycle, Generic[T]):
    """Base resource pool."""

    def __init__(self, name: str, resource_type: type[T]) -> None:
        """Initialize resource pool.

        Args:
            name: Pool name
            resource_type: Resource type
        """
        super().__init__()
        self.name = name
        self.resource_type = resource_type
        self._state = ComponentState.CREATED
        self._resources: dict[str, T] = {}
        self._available: set[str] = set()
        self._in_use: set[str] = set()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize pool."""
        try:
            self._state = ComponentState.INITIALIZING
            await self._initialize_pool()
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize pool: {e}")

    async def cleanup(self) -> None:
        """Clean up pool."""
        try:
            self._state = ComponentState.CLEANING
            await self._cleanup_pool()
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up pool: {e}")

    async def _initialize_pool(self) -> None:
        """Initialize pool implementation."""
        pass

    async def _cleanup_pool(self) -> None:
        """Clean up pool implementation."""
        pass

    async def acquire(self, resource_id: str) -> T:
        """Acquire resource.

        Args:
            resource_id: Resource ID

        Returns:
            Resource instance

        Raises:
            ValidationError: If resource not found or not available
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ValidationError(f"Resource not found: {resource_id}")
            if resource_id not in self._available:
                raise ValidationError(f"Resource not available: {resource_id}")

            self._available.remove(resource_id)
            self._in_use.add(resource_id)
            return self._resources[resource_id]

    async def release(self, resource_id: str) -> None:
        """Release resource.

        Args:
            resource_id: Resource ID

        Raises:
            ValidationError: If resource not found or not in use
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ValidationError(f"Resource not found: {resource_id}")
            if resource_id not in self._in_use:
                raise ValidationError(f"Resource not in use: {resource_id}")

            self._in_use.remove(resource_id)
            self._available.add(resource_id)

    async def add_resource(self, resource: T) -> None:
        """Add resource to pool.

        Args:
            resource: Resource to add

        Raises:
            ValidationError: If resource already exists
        """
        async with self._lock:
            if resource.id in self._resources:
                raise ValidationError(f"Resource already exists: {resource.id}")

            self._resources[resource.id] = resource
            self._available.add(resource.id)

    async def remove_resource(self, resource_id: str) -> None:
        """Remove resource from pool.

        Args:
            resource_id: Resource ID

        Raises:
            ValidationError: If resource not found or in use
        """
        async with self._lock:
            if resource_id not in self._resources:
                raise ValidationError(f"Resource not found: {resource_id}")
            if resource_id in self._in_use:
                raise ValidationError(f"Resource in use: {resource_id}")

            del self._resources[resource_id]
            self._available.remove(resource_id)


class BaseAsset(ComponentBase, Asset):
    """Base asset implementation.

    This class provides a base implementation for assets.
    """

    def __init__(
        self,
        asset_id: str,
        asset_type: AssetType,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize asset.

        Args:
            asset_id: Asset ID
            asset_type: Asset type
            metadata: Asset metadata
        """
        super().__init__()
        self._id = asset_id
        self._type = asset_type
        self._state = AssetState.CREATED
        self._metadata = AssetMetadata(
            name=asset_id, type=asset_type, **(metadata or {})
        )

        # Initialize metrics
        self._load_duration = Histogram(
            "asset_load_duration_seconds",
            "Asset load duration in seconds",
        )
        self._save_duration = Histogram(
            "asset_save_duration_seconds",
            "Asset save duration in seconds",
        )
        self._errors = Counter(
            "asset_errors_total",
            "Total number of asset errors",
        )

    @property
    def id(self) -> str:
        """Get asset ID.

        Returns:
            str: Asset ID
        """
        return self._id

    @property
    def type(self) -> AssetType:
        """Get asset type.

        Returns:
            AssetType: Asset type
        """
        return self._type

    @property
    def state(self) -> AssetState:
        """Get asset state.

        Returns:
            AssetState: Asset state
        """
        return self._state

    @property
    def metadata(self) -> AssetMetadata:
        """Get asset metadata.

        Returns:
            AssetMetadata: Asset metadata
        """
        return self._metadata

    async def load(self) -> None:
        """Load asset data."""
        try:
            self._state = AssetState.LOADING
            start = datetime.utcnow()
            await self._load()
            duration = (datetime.utcnow() - start).total_seconds()
            self._load_duration.observe(duration)
            self._state = AssetState.LOADED
        except Exception as e:
            self._state = AssetState.FAILED
            self._errors.inc()
            logger.error(
                "Failed to load asset",
                extra={
                    "asset_id": self.id,
                    "asset_type": self.type,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def save(self) -> None:
        """Save asset data."""
        try:
            start = datetime.utcnow()
            await self._save()
            duration = (datetime.utcnow() - start).total_seconds()
            self._save_duration.observe(duration)
            self._metadata.updated_at = datetime.utcnow()
        except Exception as e:
            self._errors.inc()
            logger.error(
                "Failed to save asset",
                extra={
                    "asset_id": self.id,
                    "asset_type": self.type,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def delete(self) -> None:
        """Delete asset data."""
        try:
            await self._delete()
            self._state = AssetState.DELETED
        except Exception as e:
            self._errors.inc()
            logger.error(
                "Failed to delete asset",
                extra={
                    "asset_id": self.id,
                    "asset_type": self.type,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def _load(self) -> None:
        """Load asset data implementation.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Asset loading not implemented")

    async def _save(self) -> None:
        """Save asset data implementation.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Asset saving not implemented")

    async def _delete(self) -> None:
        """Delete asset data implementation.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Asset deletion not implemented")


# Export public API
__all__ = [
    "Resource",
    "ResourceManager",
    "ResourcePool",
]
