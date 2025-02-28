"""Resource type definitions.

This module provides type definitions for the resource management system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Protocol

from pepperpy.core.common.models import BaseModel, Field


class ResourceType(str, Enum):
    """Resource type enumeration."""

    FILE = "file"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    ASSET = "asset"
    CUSTOM = "custom"


class ResourceState(str, Enum):
    """Resource state enumeration."""

    CREATED = "created"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DELETED = "deleted"


class ResourceMetadata(BaseModel):
    """Resource metadata."""

    name: str = Field(description="Resource name")
    type: ResourceType = Field(description="Resource type")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)
    size: int = Field(default=0)
    checksum: str | None = Field(default=None)
    content_type: str | None = Field(default=None)
    description: str | None = Field(default=None)
    version: str | None = Field(default=None)
    tags: set[str] = Field(default_factory=set)
    dependencies: set[str] = Field(default_factory=set)
    custom: dict[str, Any] = Field(default_factory=dict)


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


class AssetType(str, Enum):
    """Asset type enumeration."""

    MODEL = "model"
    DATASET = "dataset"
    CONFIG = "config"
    PLUGIN = "plugin"
    TEMPLATE = "template"
    CUSTOM = "custom"


class AssetState(str, Enum):
    """Asset state enumeration."""

    CREATED = "created"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DELETED = "deleted"


class AssetMetadata(BaseModel):
    """Asset metadata."""

    name: str = Field(description="Asset name")
    type: AssetType = Field(description="Asset type")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)
    size: int = Field(default=0)
    checksum: str | None = Field(default=None)
    content_type: str | None = Field(default=None)
    description: str | None = Field(default=None)
    version: str | None = Field(default=None)
    tags: set[str] = Field(default_factory=set)
    dependencies: set[str] = Field(default_factory=set)
    custom: dict[str, Any] = Field(default_factory=dict)


class Asset(Protocol):
    """Asset protocol.

    This protocol defines the interface for assets.
    """

    @property
    def id(self) -> str:
        """Get asset ID.

        Returns:
            str: Asset ID
        """
        ...

    @property
    def type(self) -> AssetType:
        """Get asset type.

        Returns:
            AssetType: Asset type
        """
        ...

    @property
    def state(self) -> AssetState:
        """Get asset state.

        Returns:
            AssetState: Asset state
        """
        ...

    @property
    def metadata(self) -> AssetMetadata:
        """Get asset metadata.

        Returns:
            AssetMetadata: Asset metadata
        """
        ...

    async def load(self) -> None:
        """Load asset data."""
        ...

    async def save(self) -> None:
        """Save asset data."""
        ...

    async def delete(self) -> None:
        """Delete asset data."""
        ...


# Export public API
__all__ = [
    "Asset",
    "AssetMetadata",
    "AssetState",
    "AssetType",
    "Resource",
    "ResourceMetadata",
    "ResourceState",
    "ResourceType",
]
