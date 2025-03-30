"""Local hub provider implementation.

This module provides a local in-memory implementation of the hub provider
interface, supporting management of AI assets with versioning.

Example:
    >>> from pepperpy.hub.providers.local import LocalHubProvider
    >>> provider = LocalHubProvider()
    >>> asset = await provider.create_asset(
    ...     name="greeting_prompt",
    ...     type="prompt",
    ...     content="Hello, I am an AI assistant.",
    ...     metadata={"language": "en"}
    ... )
    >>> assets = await provider.list_assets(type="prompt")
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pepperpy.core import NotFoundError
from pepperpy.hub.provider import (
    Asset,
    AssetStatus,
    AssetType,
    AssetVersion,
    HubError,
    HubProvider,
)

logger = logging.getLogger(__name__)


class LocalHubProvider(HubProvider):
    """Local in-memory implementation of the hub provider interface."""

    name = "local"

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize local hub provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(base_url="memory://localhost", config=config)
        self._assets: Dict[str, Asset] = {}
        self._versions: Dict[str, List[AssetVersion]] = {}

    def _validate_asset_type(self, type: Union[str, AssetType]) -> AssetType:
        """Validate and convert asset type.

        Args:
            type: Asset type string or enum

        Returns:
            AssetType enum value

        Raises:
            HubError: If type is invalid
        """
        try:
            if isinstance(type, str):
                return AssetType(type.lower())
            if isinstance(type, AssetType):
                return type
            raise ValueError(f"Invalid asset type: {type}")
        except ValueError as e:
            raise HubError(str(e))

    def _validate_asset_status(self, status: Union[str, AssetStatus]) -> AssetStatus:
        """Validate and convert asset status.

        Args:
            status: Asset status string or enum

        Returns:
            AssetStatus enum value

        Raises:
            HubError: If status is invalid
        """
        try:
            if isinstance(status, str):
                return AssetStatus(status.lower())
            if isinstance(status, AssetStatus):
                return status
            raise ValueError(f"Invalid asset status: {status}")
        except ValueError as e:
            raise HubError(str(e))

    def _validate_version(self, version: str) -> None:
        """Validate version string format.

        Args:
            version: Version string

        Raises:
            HubError: If version format is invalid
        """
        try:
            major, minor, patch = version.split(".")
            int(major)
            int(minor)
            int(patch)
        except (ValueError, AttributeError):
            raise HubError(f"Invalid version format: {version}")

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
            **kwargs: Additional options (ignored)

        Returns:
            Created asset

        Raises:
            HubError: If asset creation fails
        """
        try:
            # Validate type
            asset_type = self._validate_asset_type(type)

            # Generate asset ID and version
            asset_id = str(uuid.uuid4())
            asset_version = version or "1.0.0"
            self._validate_version(asset_version)

            # Create asset
            asset = Asset(
                id=asset_id,
                name=name,
                type=asset_type,
                content=content,
                version=asset_version,
                status=AssetStatus.DRAFT,
                metadata=metadata,
            )

            # Create version
            version_obj = AssetVersion(
                asset_id=asset_id,
                version=asset_version,
                content=content,
                metadata=metadata,
            )

            # Store asset and version
            self._assets[asset_id] = asset
            self._versions[asset_id] = [version_obj]

            return asset

        except Exception as e:
            if not isinstance(e, HubError):
                raise HubError(f"Failed to create asset: {e}")
            raise

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
            **kwargs: Additional options (ignored)

        Returns:
            Asset instance

        Raises:
            NotFoundError: If asset does not exist
            HubError: If retrieval fails
        """
        # Get asset
        asset = self._assets.get(asset_id)
        if not asset:
            raise NotFoundError(f"Asset not found: {asset_id}")

        # Return current version if no specific version requested
        if not version:
            return asset

        # Get specific version
        versions = self._versions.get(asset_id, [])
        version_obj = next(
            (v for v in versions if v.version == version),
            None,
        )
        if not version_obj:
            raise NotFoundError(f"Version not found: {version}")

        # Create asset copy with version content
        return Asset(
            id=asset.id,
            name=asset.name,
            type=asset.type,
            content=version_obj.content,
            version=version_obj.version,
            status=asset.status,
            created_at=asset.created_at,
            updated_at=version_obj.created_at,
            metadata=version_obj.metadata or asset.metadata,
        )

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
            **kwargs: Additional options (ignored)

        Returns:
            Updated asset

        Raises:
            NotFoundError: If asset does not exist
            HubError: If update fails
        """
        # Get asset
        asset = await self.get_asset(asset_id)

        try:
            # Generate new version
            if version:
                self._validate_version(version)
                new_version = version
            else:
                # Increment patch version
                major, minor, patch = asset.version.split(".")
                new_version = f"{major}.{minor}.{int(patch) + 1}"

            # Create version
            version_obj = AssetVersion(
                asset_id=asset_id,
                version=new_version,
                content=content,
                metadata=metadata,
            )

            # Update asset
            asset.content = content
            asset.version = new_version
            asset.updated_at = datetime.now()
            if metadata:
                if asset.metadata:
                    asset.metadata.update(metadata)
                else:
                    asset.metadata = metadata

            # Store version
            self._versions[asset_id].append(version_obj)

            return asset

        except Exception as e:
            if not isinstance(e, (NotFoundError, HubError)):
                raise HubError(f"Failed to update asset: {e}")
            raise

    async def delete_asset(
        self,
        asset_id: str,
        **kwargs: Any,
    ) -> None:
        """Delete an asset.

        Args:
            asset_id: Asset identifier
            **kwargs: Additional options (ignored)

        Raises:
            NotFoundError: If asset does not exist
            HubError: If deletion fails
        """
        # Check if asset exists
        if asset_id not in self._assets:
            raise NotFoundError(f"Asset not found: {asset_id}")

        try:
            # Delete asset and versions
            del self._assets[asset_id]
            del self._versions[asset_id]

        except Exception as e:
            if not isinstance(e, NotFoundError):
                raise HubError(f"Failed to delete asset: {e}")
            raise

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
            **kwargs: Additional options (ignored)

        Returns:
            List of assets

        Raises:
            HubError: If listing fails
        """
        try:
            assets = list(self._assets.values())

            # Apply type filter
            if type:
                types = [type] if not isinstance(type, list) else type
                valid_types = [self._validate_asset_type(t) for t in types]
                assets = [a for a in assets if a.type in valid_types]

            # Apply status filter
            if status:
                statuses = [status] if not isinstance(status, list) else status
                valid_statuses = [self._validate_asset_status(s) for s in statuses]
                assets = [a for a in assets if a.status in valid_statuses]

            return assets

        except Exception as e:
            if not isinstance(e, HubError):
                raise HubError(f"Failed to list assets: {e}")
            raise

    async def get_asset_versions(
        self,
        asset_id: str,
        **kwargs: Any,
    ) -> List[AssetVersion]:
        """Get version history for an asset.

        Args:
            asset_id: Asset identifier
            **kwargs: Additional options (ignored)

        Returns:
            List of asset versions

        Raises:
            NotFoundError: If asset does not exist
            HubError: If retrieval fails
        """
        # Check if asset exists
        if asset_id not in self._assets:
            raise NotFoundError(f"Asset not found: {asset_id}")

        # Get versions
        versions = self._versions.get(asset_id, [])
        return sorted(versions, key=lambda v: v.version)

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
            **kwargs: Additional options (ignored)

        Returns:
            Published asset

        Raises:
            NotFoundError: If asset does not exist
            HubError: If publish fails
        """
        # Get asset
        asset = await self.get_asset(asset_id, version)

        try:
            # Update status and metadata
            asset.status = AssetStatus.PUBLISHED
            asset.updated_at = datetime.now()
            if metadata:
                if asset.metadata:
                    asset.metadata.update(metadata)
                else:
                    asset.metadata = metadata

            return asset

        except Exception as e:
            if not isinstance(e, (NotFoundError, HubError)):
                raise HubError(f"Failed to publish asset: {e}")
            raise

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
            **kwargs: Additional options (ignored)

        Returns:
            Archived asset

        Raises:
            NotFoundError: If asset does not exist
            HubError: If archive fails
        """
        # Get asset
        asset = await self.get_asset(asset_id)

        try:
            # Update status and metadata
            asset.status = AssetStatus.ARCHIVED
            asset.updated_at = datetime.now()
            if metadata:
                if asset.metadata:
                    asset.metadata.update(metadata)
                else:
                    asset.metadata = metadata

            return asset

        except Exception as e:
            if not isinstance(e, (NotFoundError, HubError)):
                raise HubError(f"Failed to archive asset: {e}")
            raise

    def get_capabilities(self) -> Dict[str, Any]:
        """Get local hub provider capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            "max_size": None,  # No limit
            "supports_versioning": True,
            "supports_metadata": True,
            "supports_filters": True,
        })
        return capabilities
