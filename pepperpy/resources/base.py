"""Base resource management system.

This module provides a unified system for managing resources and assets.
"""

import asyncio
import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Set

from pepperpy.core.base import ComponentBase
from pepperpy.core.errors import ResourceError
from pepperpy.core.metrics import Counter, Histogram
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
    expires_at: Optional[datetime] = None
    size: int = 0
    checksum: Optional[str] = None
    content_type: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)


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
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
        custom: Optional[Dict[str, Any]] = None,
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


class ResourceManager(ComponentBase):
    """Resource manager implementation.

    This class provides methods for managing resources.
    """

    def __init__(self) -> None:
        """Initialize manager."""
        super().__init__()
        self._resources: Dict[str, Resource] = {}
        self._lock = asyncio.Lock()

        # Initialize metrics
        self._resources_loaded = Counter(
            "resources_loaded_total", "Total number of resources loaded"
        )
        self._resources_saved = Counter(
            "resources_saved_total", "Total number of resources saved"
        )
        self._resource_errors = Counter(
            "resource_errors_total", "Total number of resource errors"
        )
        self._resource_size = Histogram("resource_size_bytes", "Resource size in bytes")

    async def register_resource(self, resource: Resource) -> None:
        """Register resource.

        Args:
            resource: Resource to register

        Raises:
            ResourceError: If resource already exists
        """
        async with self._lock:
            if resource.id in self._resources:
                raise ResourceError(f"Resource already exists: {resource.id}")
            self._resources[resource.id] = resource

    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Optional[Resource]: Resource if found
        """
        return self._resources.get(resource_id)

    async def list_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        tags: Optional[Set[str]] = None,
    ) -> List[Resource]:
        """List resources.

        Args:
            resource_type: Filter by resource type
            tags: Filter by tags

        Returns:
            List[Resource]: List of resources
        """
        resources = list(self._resources.values())

        if resource_type:
            resources = [r for r in resources if r.type == resource_type]

        if tags:
            resources = [r for r in resources if tags.issubset(r.metadata.tags)]

        return resources

    async def delete_resource(self, resource_id: str) -> None:
        """Delete resource.

        Args:
            resource_id: Resource ID

        Raises:
            ResourceError: If resource not found
        """
        async with self._lock:
            resource = self._resources.get(resource_id)
            if not resource:
                raise ResourceError(f"Resource not found: {resource_id}")

            await resource.delete()
            del self._resources[resource_id]


class BaseAsset(ComponentBase, Asset):
    """Base asset implementation.

    This class provides a base implementation for assets.
    """

    def __init__(
        self,
        asset_id: str,
        asset_type: AssetType,
        metadata: Optional[Dict[str, Any]] = None,
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
        self._metadata = AssetMetadata()

        # Update metadata if provided
        if metadata:
            for key, value in metadata.items():
                if hasattr(self._metadata, key):
                    setattr(self._metadata, key, value)
                else:
                    self._metadata.custom[key] = value

        # Initialize metrics
        self._load_duration = Histogram(
            "asset_load_duration_seconds",
            "Asset load duration in seconds",
            labels={"asset_type": self._type.value},
        )
        self._save_duration = Histogram(
            "asset_save_duration_seconds",
            "Asset save duration in seconds",
            labels={"asset_type": self._type.value},
        )
        self._errors = Counter(
            "asset_errors_total",
            "Total number of asset errors",
            labels={"asset_type": self._type.value},
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
            with self._load_duration.time():
                await self._load()
            self._state = AssetState.LOADED
        except Exception as e:
            self._state = AssetState.FAILED
            self._errors.inc()
            logger.error(
                f"Failed to load asset: {e}",
                extra={
                    "asset_id": self.id,
                    "asset_type": self.type.value,
                },
                exc_info=True,
            )
            raise ResourceError(f"Failed to load asset: {e}")

    async def save(self) -> None:
        """Save asset data."""
        try:
            with self._save_duration.time():
                await self._save()
            self._metadata.updated_at = datetime.now()
        except Exception as e:
            self._errors.inc()
            logger.error(
                f"Failed to save asset: {e}",
                extra={
                    "asset_id": self.id,
                    "asset_type": self.type.value,
                },
                exc_info=True,
            )
            raise ResourceError(f"Failed to save asset: {e}")

    async def delete(self) -> None:
        """Delete asset data."""
        try:
            await self._delete()
            self._state = AssetState.DELETED
        except Exception as e:
            self._errors.inc()
            logger.error(
                f"Failed to delete asset: {e}",
                extra={
                    "asset_id": self.id,
                    "asset_type": self.type.value,
                },
                exc_info=True,
            )
            raise ResourceError(f"Failed to delete asset: {e}")

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
