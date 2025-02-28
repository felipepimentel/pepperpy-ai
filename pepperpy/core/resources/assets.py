"""Asset management module.

This module provides a unified system for managing assets.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import Field

from pepperpy.common.base import ComponentBase
from pepperpy.core.errors import AssetError
from pepperpy.common.metrics import Counter, Histogram
from pepperpy.common.resources import Resource, ResourceManager, ResourceMetadata
from pepperpy.core.types import ResourceType

# Configure logging
logger = logging.getLogger(__name__)


class AssetMetadata(ResourceMetadata):
    """Asset metadata model.

    This class extends ResourceMetadata with asset-specific fields.
    """

    category: str = Field(..., description="Asset category")
    scope: str = Field(..., description="Asset scope")
    owner: str = Field(..., description="Asset owner")
    status: str = Field("active", description="Asset status")
    expiration: Optional[datetime] = Field(None, description="Asset expiration")
    permissions: Set[str] = Field(default_factory=set, description="Asset permissions")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Asset attributes"
    )


class Asset(Resource):
    """Asset model.

    This class extends Resource with asset-specific functionality.
    """

    metadata: AssetMetadata = Field(..., description="Asset metadata")
    preview: Optional[bytes] = Field(None, description="Asset preview")
    thumbnail: Optional[bytes] = Field(None, description="Asset thumbnail")
    manifest: Optional[Dict[str, Any]] = Field(None, description="Asset manifest")


class AssetManager(ComponentBase):
    """Asset manager implementation.

    This class provides methods for managing assets.
    """

    def __init__(self) -> None:
        """Initialize manager."""
        super().__init__()
        self._resource_manager = ResourceManager()
        self._assets: Dict[str, Asset] = {}
        self._lock = asyncio.Lock()

        # Initialize metrics
        self._assets_loaded = Counter(
            "assets_loaded_total", "Total number of assets loaded"
        )
        self._assets_saved = Counter(
            "assets_saved_total", "Total number of assets saved"
        )
        self._asset_errors = Counter(
            "asset_errors_total", "Total number of asset errors"
        )
        self._asset_size = Histogram("asset_size_bytes", "Asset size in bytes")

    async def load_asset(
        self,
        path: Union[str, Path],
        category: str,
        scope: str,
        owner: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Asset:
        """Load asset from path.

        Args:
            path: Asset path
            category: Asset category
            scope: Asset scope
            owner: Asset owner
            metadata: Additional metadata

        Returns:
            Asset: Loaded asset

        Raises:
            AssetError: If asset cannot be loaded
        """
        try:
            path = Path(path)
            if not path.exists():
                raise AssetError(f"Asset not found: {path}")

            async with self._lock:
                if str(path) in self._assets:
                    return self._assets[str(path)]

                # Load resource
                resource = await self._resource_manager.load_resource(
                    path,
                    resource_type=ResourceType.ASSET,
                    metadata=metadata,
                )

                # Create asset metadata
                asset_metadata = AssetMetadata(
                    name=resource.metadata.name,
                    type=resource.metadata.type,
                    description=resource.metadata.description,
                    version=resource.metadata.version,
                    created=resource.metadata.created,
                    updated=resource.metadata.updated,
                    tags=resource.metadata.tags,
                    dependencies=resource.metadata.dependencies,
                    metadata=resource.metadata.metadata,
                    category=category,
                    scope=scope,
                    owner=owner,
                )

                # Create asset
                asset = Asset(
                    metadata=asset_metadata,
                    content=resource.content,
                    path=resource.path,
                    size=resource.size,
                    format=resource.format,
                    checksum=resource.checksum,
                    encoding=resource.encoding,
                    compression=resource.compression,
                    encrypted=resource.encrypted,
                )

                # Generate preview and thumbnail
                if asset.format in {"png", "jpg", "jpeg", "gif"}:
                    await self._generate_image_previews(asset)
                elif asset.format in {"pdf", "doc", "docx"}:
                    await self._generate_document_previews(asset)

                # Update metrics
                self._assets_loaded.inc()
                self._asset_size.observe(asset.size or 0)

                # Cache asset
                self._assets[str(path)] = asset
                return asset

        except Exception as e:
            self._asset_errors.inc()
            logger.error(
                f"Failed to load asset: {e}",
                extra={
                    "path": str(path),
                    "category": category,
                    "scope": scope,
                    "owner": owner,
                },
                exc_info=True,
            )
            raise AssetError(f"Failed to load asset: {e}") from e

    async def save_asset(
        self,
        asset: Asset,
        path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Save asset to path.

        Args:
            asset: Asset to save
            path: Target path (defaults to asset.path)

        Raises:
            AssetError: If asset cannot be saved
        """
        try:
            # Save resource
            await self._resource_manager.save_resource(asset, path)

            # Update asset
            if path:
                asset.path = Path(path)
            asset.metadata.updated = datetime.utcnow()

            # Update metrics
            self._assets_saved.inc()
            self._asset_size.observe(asset.size or 0)

            # Cache asset
            self._assets[str(asset.path)] = asset

        except Exception as e:
            self._asset_errors.inc()
            logger.error(
                f"Failed to save asset: {e}",
                extra={
                    "path": str(path or asset.path),
                    "category": asset.metadata.category,
                    "scope": asset.metadata.scope,
                    "owner": asset.metadata.owner,
                },
                exc_info=True,
            )
            raise AssetError(f"Failed to save asset: {e}") from e

    async def get_asset(
        self,
        path: Union[str, Path],
    ) -> Optional[Asset]:
        """Get asset by path.

        Args:
            path: Asset path

        Returns:
            Optional[Asset]: Asset if found
        """
        return self._assets.get(str(Path(path)))

    async def list_assets(
        self,
        category: Optional[str] = None,
        scope: Optional[str] = None,
        owner: Optional[str] = None,
        tags: Optional[Set[str]] = None,
    ) -> List[Asset]:
        """List assets.

        Args:
            category: Filter by category
            scope: Filter by scope
            owner: Filter by owner
            tags: Filter by tags

        Returns:
            List[Asset]: List of assets
        """
        assets = list(self._assets.values())

        if category:
            assets = [a for a in assets if a.metadata.category == category]

        if scope:
            assets = [a for a in assets if a.metadata.scope == scope]

        if owner:
            assets = [a for a in assets if a.metadata.owner == owner]

        if tags:
            assets = [a for a in assets if tags.issubset(a.metadata.tags)]

        return assets

    async def delete_asset(
        self,
        path: Union[str, Path],
    ) -> None:
        """Delete asset.

        Args:
            path: Asset path

        Raises:
            AssetError: If asset cannot be deleted
        """
        try:
            # Delete resource
            await self._resource_manager.delete_resource(path)

            # Remove from cache
            self._assets.pop(str(Path(path)), None)

        except Exception as e:
            self._asset_errors.inc()
            logger.error(
                f"Failed to delete asset: {e}",
                extra={"path": str(path)},
                exc_info=True,
            )
            raise AssetError(f"Failed to delete asset: {e}") from e

    async def _generate_image_previews(self, asset: Asset) -> None:
        """Generate image previews.

        Args:
            asset: Asset to generate previews for
        """
        # TODO: Implement image preview generation
        pass

    async def _generate_document_previews(self, asset: Asset) -> None:
        """Generate document previews.

        Args:
            asset: Asset to generate previews for
        """
        # TODO: Implement document preview generation
        pass
