"""Hub provider interface for PepperPy.

This module provides the base classes and interfaces for hub providers,
supporting management of AI assets like prompts, agents, and workflows.

Example:
    >>> from pepperpy.hub import HubProvider, Asset
    >>> provider = HubProvider.from_config({
    ...     "provider": "local",
    ...     "storage": "memory"
    ... })
    >>> asset = await provider.create_asset(
    ...     name="greeting_prompt",
    ...     type="prompt",
    ...     content="Hello, I am an AI assistant.",
    ...     metadata={"language": "en"}
    ... )
    >>> assets = await provider.list_assets(type="prompt")
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pepperpy.common.providers import RestProvider
from pepperpy.core.errors import PepperPyError

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    """Type of AI asset."""

    PROMPT = "prompt"
    AGENT = "agent"
    WORKFLOW = "workflow"
    DATASET = "dataset"
    MODEL = "model"
    CONFIG = "config"


class AssetStatus(str, Enum):
    """Status of an AI asset."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


@dataclass
class Asset:
    """An AI asset stored in the hub.

    Args:
        id: Asset identifier
        name: Asset name
        type: Asset type
        content: Asset content
        version: Asset version
        status: Asset status
        created_at: Creation timestamp
        updated_at: Last update timestamp
        metadata: Optional asset metadata
            - description: Asset description
            - author: Asset author
            - tags: Asset tags
            - custom: Additional metadata fields

    Example:
        >>> asset = Asset(
        ...     id="asset_123",
        ...     name="greeting_prompt",
        ...     type=AssetType.PROMPT,
        ...     content="Hello, I am an AI assistant.",
        ...     version="1.0.0",
        ...     status=AssetStatus.PUBLISHED,
        ...     metadata={"language": "en"}
        ... )
    """

    id: str
    name: str
    type: AssetType
    content: Any
    version: str
    status: AssetStatus = AssetStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AssetVersion:
    """Version information for an AI asset.

    Args:
        asset_id: Asset identifier
        version: Version string
        content: Version content
        created_at: Creation timestamp
        metadata: Optional version metadata
            - changelog: Version changes
            - author: Version author
            - custom: Additional metadata fields

    Example:
        >>> version = AssetVersion(
        ...     asset_id="asset_123",
        ...     version="1.0.0",
        ...     content="Hello, I am an AI assistant.",
        ...     metadata={"changelog": "Initial version"}
        ... )
    """

    asset_id: str
    version: str
    content: Any
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class HubError(PepperPyError):
    """Base exception for hub-related errors."""

    pass


class HubProvider(RestProvider):
    """Base class for hub providers."""

    def __init__(
        self,
        base_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize hub provider.

        Args:
            base_url: Base URL for the REST API
            config: Optional configuration dictionary
        """
        super().__init__(base_url=base_url, config=config)

    @abstractmethod
    async def create_asset(
        self,
        name: str,
        type: Union[str, AssetType],
        content: Any,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Asset:
        """Create a new asset.

        Args:
            name: Asset name
            type: Asset type
            content: Asset content
            version: Optional version string
            metadata: Optional asset metadata
            **kwargs: Additional provider-specific arguments

        Returns:
            Created asset

        Raises:
            HubError: If asset creation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def get_asset(
        self,
        asset_id: str,
        version: Optional[str] = None,
        **kwargs: Any,
    ) -> Asset:
        """Get asset by ID.

        Args:
            asset_id: Asset identifier
            version: Optional version to retrieve
            **kwargs: Additional provider-specific arguments

        Returns:
            Asset instance

        Raises:
            NotFoundError: If asset does not exist
            HubError: If retrieval fails
        """
        raise NotImplementedError

    @abstractmethod
    async def update_asset(
        self,
        asset_id: str,
        content: Any,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Asset:
        """Update an existing asset.

        Args:
            asset_id: Asset identifier
            content: New asset content
            version: Optional new version
            metadata: Optional metadata updates
            **kwargs: Additional provider-specific arguments

        Returns:
            Updated asset

        Raises:
            NotFoundError: If asset does not exist
            HubError: If update fails
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_asset(
        self,
        asset_id: str,
        **kwargs: Any,
    ) -> None:
        """Delete an asset.

        Args:
            asset_id: Asset identifier
            **kwargs: Additional provider-specific arguments

        Raises:
            NotFoundError: If asset does not exist
            HubError: If deletion fails
        """
        raise NotImplementedError

    @abstractmethod
    async def list_assets(
        self,
        type: Optional[Union[str, AssetType, List[Union[str, AssetType]]]] = None,
        status: Optional[Union[str, AssetStatus, List[Union[str, AssetStatus]]]] = None,
        **kwargs: Any,
    ) -> List[Asset]:
        """List assets with optional filters.

        Args:
            type: Optional type or types to filter by
            status: Optional status or statuses to filter by
            **kwargs: Additional provider-specific arguments

        Returns:
            List of assets

        Raises:
            HubError: If listing fails
        """
        raise NotImplementedError

    @abstractmethod
    async def get_asset_versions(
        self,
        asset_id: str,
        **kwargs: Any,
    ) -> List[AssetVersion]:
        """Get version history for an asset.

        Args:
            asset_id: Asset identifier
            **kwargs: Additional provider-specific arguments

        Returns:
            List of asset versions

        Raises:
            NotFoundError: If asset does not exist
            HubError: If retrieval fails
        """
        raise NotImplementedError

    @abstractmethod
    async def publish_asset(
        self,
        asset_id: str,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Asset:
        """Publish an asset version.

        Args:
            asset_id: Asset identifier
            version: Optional version to publish
            metadata: Optional publish metadata
            **kwargs: Additional provider-specific arguments

        Returns:
            Published asset

        Raises:
            NotFoundError: If asset does not exist
            HubError: If publish fails
        """
        raise NotImplementedError

    @abstractmethod
    async def archive_asset(
        self,
        asset_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Asset:
        """Archive an asset.

        Args:
            asset_id: Asset identifier
            metadata: Optional archive metadata
            **kwargs: Additional provider-specific arguments

        Returns:
            Archived asset

        Raises:
            NotFoundError: If asset does not exist
            HubError: If archive fails
        """
        raise NotImplementedError

    def get_capabilities(self) -> Dict[str, Any]:
        """Get hub provider capabilities.

        Returns:
            Dictionary containing:
                - supported_types: List of supported asset types
                - max_size: Maximum asset size in bytes
                - supports_versioning: Whether versioning is supported
                - additional provider-specific capabilities
        """
        return {
            "supported_types": [t.value for t in AssetType],
            "max_size": 0,
            "supports_versioning": False,
        }
