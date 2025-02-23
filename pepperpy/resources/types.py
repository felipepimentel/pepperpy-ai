"""Resource types module.

This module provides type definitions for resources and assets.
"""

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, Set, Type, TypeVar

from pepperpy.core.base import ComponentBase
from pepperpy.core.errors import ResourceError


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

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    size: int = 0
    checksum: Optional[str] = None
    content_type: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
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


class AssetType(enum.Enum):
    """Asset type enumeration."""

    MODEL = "model"
    PROMPT = "prompt"
    CONFIG = "config"
    DATA = "data"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    CUSTOM = "custom"


class AssetState(enum.Enum):
    """Asset state enumeration."""

    CREATED = "created"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass
class AssetMetadata:
    """Asset metadata class."""

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)


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