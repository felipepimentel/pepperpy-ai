"""Asset management system.

This module provides functionality for managing AI assets.
"""

import asyncio
import enum
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.core.errors import ResourceError
from pepperpy.resources.base import BaseResource, ResourceType
from pepperpy.resources.storage import FileResource, ResourceStorage

# Configure logging
logger = logging.getLogger(__name__)


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


class Asset(BaseResource):
    """Asset implementation.

    This class provides a base implementation for AI assets.
    """

    def __init__(
        self,
        id: str,
        asset_type: AssetType,
        path: Optional[Union[str, Path]] = None,
        content: Optional[Any] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        license: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
        custom: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize asset.

        Args:
            id: Asset ID
            asset_type: Asset type
            path: Asset path
            content: Asset content
            version: Asset version
            description: Asset description
            author: Asset author
            license: Asset license
            tags: Asset tags
            dependencies: Asset dependencies
            custom: Custom metadata
        """
        super().__init__(
            id,
            ResourceType.ASSET,
            name=id,
            description=description,
            version=version,
            tags=tags,
            dependencies=dependencies,
            custom=custom or {},
        )
        self._asset_type = asset_type
        self._path = Path(path) if path else None
        self._content = content
        self.metadata.custom.update({
            "asset_type": asset_type.value,
            "author": author,
            "license": license,
        })

    @property
    def asset_type(self) -> AssetType:
        """Get asset type."""
        return self._asset_type

    @property
    def path(self) -> Optional[Path]:
        """Get asset path."""
        return self._path

    @property
    def content(self) -> Optional[Any]:
        """Get asset content."""
        return self._content

    async def _load(self) -> None:
        """Load asset data."""
        if self._path is None:
            return

        try:
            # Load using file resource
            resource = FileResource(
                self.id,
                self._path,
                content_type=self._path.suffix.lstrip("."),
            )
            await resource.load()
            self._content = resource.content
            self.metadata.size = resource.metadata.size
            self.metadata.updated_at = datetime.utcnow()
        except Exception as e:
            raise ResourceError(f"Failed to load asset {self.id}: {e}") from e

    async def _save(self) -> None:
        """Save asset data."""
        if self._path is None or self._content is None:
            return

        try:
            # Save using file resource
            resource = FileResource(
                self.id,
                self._path,
                content_type=self._path.suffix.lstrip("."),
            )
            resource._content = self._content
            await resource.save()
            self.metadata.size = resource.metadata.size
            self.metadata.updated_at = datetime.utcnow()
        except Exception as e:
            raise ResourceError(f"Failed to save asset {self.id}: {e}") from e

    async def _delete(self) -> None:
        """Delete asset data."""
        if self._path is None:
            return

        try:
            # Delete using file resource
            resource = FileResource(
                self.id,
                self._path,
                content_type=self._path.suffix.lstrip("."),
            )
            await resource.delete()
            self._content = None
            self.metadata.size = 0
        except Exception as e:
            raise ResourceError(f"Failed to delete asset {self.id}: {e}") from e

    async def _initialize(self) -> None:
        """Initialize asset."""
        pass

    async def _execute(self) -> None:
        """Execute asset."""
        pass

    async def _cleanup(self) -> None:
        """Clean up asset."""
        await self.delete()


class AssetManager:
    """Asset manager implementation.

    This class provides methods for managing AI assets.
    """

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize manager.

        Args:
            base_path: Base path for assets
        """
        self._base_path = Path(base_path) if base_path else Path.cwd() / "assets"
        self._storage = ResourceStorage(self._base_path)
        self._assets: Dict[str, Asset] = {}
        self._lock = asyncio.Lock()

    async def create_asset(
        self,
        id: str,
        asset_type: AssetType,
        content: Optional[Any] = None,
        path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> Asset:
        """Create asset.

        Args:
            id: Asset ID
            asset_type: Asset type
            content: Asset content
            path: Asset path
            **kwargs: Additional metadata

        Returns:
            Asset: Created asset

        Raises:
            ResourceError: If asset already exists
        """
        async with self._lock:
            if id in self._assets:
                raise ResourceError(f"Asset already exists: {id}")

            # Create asset
            asset = Asset(
                id,
                asset_type,
                path=path or self._base_path / f"{id}.{asset_type.value}",
                content=content,
                **kwargs,
            )

            # Save asset
            if content is not None:
                await asset.save()

            self._assets[id] = asset
            return asset

    async def get_asset(self, id: str) -> Optional[Asset]:
        """Get asset.

        Args:
            id: Asset ID

        Returns:
            Optional[Asset]: Asset if found
        """
        return self._assets.get(id)

    async def list_assets(
        self,
        asset_type: Optional[AssetType] = None,
        tags: Optional[Set[str]] = None,
    ) -> List[Asset]:
        """List assets.

        Args:
            asset_type: Filter by asset type
            tags: Filter by tags

        Returns:
            List[Asset]: List of assets
        """
        assets = list(self._assets.values())

        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]

        if tags:
            assets = [a for a in assets if tags.issubset(a.metadata.tags)]

        return assets

    async def delete_asset(self, id: str) -> None:
        """Delete asset.

        Args:
            id: Asset ID

        Raises:
            ResourceError: If asset not found
        """
        async with self._lock:
            asset = self._assets.get(id)
            if not asset:
                raise ResourceError(f"Asset not found: {id}")

            await asset.delete()
            del self._assets[id]
