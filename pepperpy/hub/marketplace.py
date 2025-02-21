"""Marketplace module for the Pepperpy Hub.

This module provides functionality for interacting with the Pepperpy marketplace,
including artifact discovery, installation, and management.
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import PepperpyError
from pepperpy.core.types import ComponentState
from pepperpy.hub.errors import HubError, HubMarketplaceError
from pepperpy.hub.security import SecurityManager
from pepperpy.hub.storage import StorageBackend, StorageMetadata
from pepperpy.monitoring import logger


class MarketplaceConfig(BaseModel):
    """Configuration for the marketplace."""

    api_url: str = Field(
        default="https://marketplace.pepperpy.ai",
        description="URL of the marketplace API",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for marketplace authentication",
    )
    timeout: int = Field(
        default=30,
        description="Timeout for marketplace API requests in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests",
    )
    retry_delay: int = Field(
        default=1,
        description="Delay between retries in seconds",
    )


class MarketplaceManager(Lifecycle):
    """Manager for marketplace operations."""

    def __init__(
        self,
        config: MarketplaceConfig,
        storage: StorageBackend,
        security: SecurityManager,
    ) -> None:
        """Initialize marketplace manager.

        Args:
            config: Marketplace configuration
            storage: Storage backend
            security: Security manager
        """
        self.config = config
        self.storage = storage
        self.security = security
        self._session: Optional[aiohttp.ClientSession] = None
        self._state = ComponentState.INITIALIZED
        logger.debug("Initialized marketplace manager")

    async def initialize(self) -> None:
        """Initialize the marketplace manager.

        This:
        1. Validates configuration
        2. Sets up HTTP session
        3. Initializes caches

        Raises:
            HubError: If initialization fails
        """
        try:
            # Validate config
            if self.config.api_key and not self.config.api_url:
                raise HubError("API URL required when API key is provided")

            # Setup session
            self._session = aiohttp.ClientSession(
                base_url=self.config.api_url,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                if self.config.api_key
                else None,
            )

            # Update state
            self._state = ComponentState.RUNNING
            logger.info("Marketplace manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize marketplace manager: {e}")
            raise HubError("Failed to initialize marketplace manager") from e

    async def cleanup(self) -> None:
        """Clean up marketplace manager resources.

        This:
        1. Closes HTTP session
        2. Cleans up caches

        Raises:
            HubError: If cleanup fails
        """
        try:
            if self._session:
                await self._session.close()

            # Update state
            self._state = ComponentState.UNREGISTERED
            logger.info("Marketplace manager cleaned up")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup marketplace manager: {e}")
            raise HubError("Failed to cleanup marketplace manager") from e

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make an API request with retries.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Dict[str, Any]: Response data

        Raises:
            HubMarketplaceError: If request fails
        """
        if not self._session:
            raise HubMarketplaceError("API client not initialized")

        url = urljoin(self.config.api_url, endpoint)
        retries = 0

        while retries <= self.config.max_retries:
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(
                            response.headers.get("Retry-After", self.config.retry_delay)
                        )
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue

                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                if retries == self.config.max_retries:
                    raise HubMarketplaceError(f"API request failed: {e}")
                retries += 1
                await asyncio.sleep(self.config.retry_delay)

        raise HubMarketplaceError("Max retries exceeded")

    async def publish_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: StorageMetadata,
        visibility: str = "public",
    ) -> str:
        """Publish an artifact to the marketplace.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact.
            content: Artifact content.
            metadata: Artifact metadata.
            visibility: Visibility level (public, private, shared).

        Returns:
            str: Marketplace ID for the published artifact.

        Raises:
            PepperpyError: If publishing fails.
        """
        try:
            # Validate artifact
            await self.security.validate_artifact(
                artifact_type=artifact_type,
                content=content,
                metadata=metadata.dict(),  # Convert to dictionary
            )

            # Store artifact locally
            await self.storage.store(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                content=content,
                metadata=metadata,
            )

            # Publish to marketplace
            response = await self._make_request(
                method="POST",
                endpoint=f"/v1/artifacts/{artifact_type}",
                json={
                    "artifact_id": artifact_id,
                    "content": content,
                    "metadata": metadata.dict(),
                    "visibility": visibility,
                },
            )

            marketplace_id = response["marketplace_id"]
            logger.info(f"Published artifact {artifact_id} to marketplace")
            return marketplace_id

        except Exception as e:
            raise PepperpyError(
                f"Failed to publish artifact {artifact_id}: {str(e)}",
                recovery_hint="Check your marketplace configuration and credentials",
            )

    async def install_artifact(
        self,
        artifact_id: str,
        version: Optional[str] = None,
    ) -> None:
        """Install an artifact from the marketplace.

        Args:
            artifact_id: ID of the artifact to install.
            version: Specific version to install.

        Raises:
            PepperpyError: If installation fails.
        """
        try:
            # Get artifact details
            endpoint = f"/v1/artifacts/{artifact_id}"
            if version:
                endpoint += f"/versions/{version}"

            response = await self._make_request("GET", endpoint)
            artifact_data = response["artifact"]

            # Validate artifact
            await self.security.validate_artifact(
                artifact_type=artifact_data["type"],
                content=artifact_data["content"],
                metadata=artifact_data["metadata"],
            )

            # Store locally
            await self.storage.store(
                artifact_id=artifact_id,
                artifact_type=artifact_data["type"],
                content=artifact_data["content"],
                metadata=StorageMetadata(**artifact_data["metadata"]),
            )

            logger.info(
                f"Installed artifact {artifact_id}"
                + (f" version {version}" if version else "")
            )

        except Exception as e:
            raise PepperpyError(
                f"Failed to install artifact {artifact_id}: {str(e)}",
                recovery_hint="Check if the artifact exists and you have access",
            )

    async def search(
        self,
        query: str,
        artifact_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """Search for artifacts in the marketplace.

        Args:
            query: Search query.
            artifact_type: Filter by artifact type.
            tags: Filter by tags.
            page: Page number for pagination.
            per_page: Number of results per page.

        Returns:
            Dict containing search results and pagination info.

        Raises:
            PepperpyError: If search fails.
        """
        try:
            params = {
                "q": query,
                "page": page,
                "per_page": per_page,
            }
            if artifact_type:
                params["type"] = artifact_type
            if tags:
                params["tags"] = ",".join(tags)

            response = await self._make_request(
                method="GET",
                endpoint="/v1/search",
                params=params,
            )

            return {
                "artifacts": response["artifacts"],
                "total": response["total"],
                "total_pages": response["total_pages"],
                "page": response["page"],
                "per_page": response["per_page"],
            }

        except Exception as e:
            raise PepperpyError(
                f"Failed to search marketplace: {str(e)}",
                recovery_hint="Check your marketplace configuration and network connection",
            )

    async def get_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """Get detailed information about an artifact.

        Args:
            artifact_id: ID of the artifact.

        Returns:
            Dict containing artifact details.

        Raises:
            PepperpyError: If retrieval fails.
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/v1/artifacts/{artifact_id}",
            )
            return response["artifact"]

        except Exception as e:
            raise PepperpyError(
                f"Failed to get artifact {artifact_id}: {str(e)}",
                recovery_hint="Check if the artifact exists and you have access",
            )

    async def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact from the marketplace.

        Args:
            artifact_id: ID of the artifact to delete.

        Raises:
            PepperpyError: If deletion fails.
        """
        try:
            await self._make_request(
                method="DELETE",
                endpoint=f"/v1/artifacts/{artifact_id}",
            )
            logger.info(f"Deleted artifact {artifact_id} from marketplace")

        except Exception as e:
            raise PepperpyError(
                f"Failed to delete artifact {artifact_id}: {str(e)}",
                recovery_hint="Check if you have permission to delete this artifact",
            )
