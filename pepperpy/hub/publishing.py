"""Publishing module for the Pepperpy Hub.

This module provides functionality for publishing artifacts to the Hub,
including validation, versioning, and metadata management.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from pepperpy.hub.errors import HubPublishingError, HubValidationError
from pepperpy.hub.marketplace import MarketplaceManager
from pepperpy.hub.security import SecurityManager
from pepperpy.hub.storage import StorageBackend, StorageMetadata
from pepperpy.monitoring.audit import audit_logger


class PublishConfig(BaseModel):
    """Publishing configuration."""

    require_version: bool = Field(
        default=True,
        description="Whether version is required",
    )
    require_description: bool = Field(
        default=True,
        description="Whether description is required",
    )
    require_author: bool = Field(
        default=True,
        description="Whether author is required",
    )
    allowed_visibilities: Set[str] = Field(
        default_factory=lambda: {"public", "private", "shared"},
        description="Allowed visibility levels",
    )


class Publisher:
    """Publisher for Hub artifacts."""

    def __init__(
        self,
        storage: StorageBackend,
        security: SecurityManager,
        marketplace: MarketplaceManager,
        config: Optional[PublishConfig] = None,
    ) -> None:
        """Initialize publisher.

        Args:
            storage: Storage backend
            security: Security manager
            marketplace: Marketplace manager
            config: Optional publishing configuration
        """
        self.storage = storage
        self.security = security
        self.marketplace = marketplace
        self.config = config or PublishConfig()

    async def validate_metadata(
        self,
        metadata: Dict[str, Any],
        artifact_type: str,
    ) -> None:
        """Validate artifact metadata.

        Args:
            metadata: Metadata to validate
            artifact_type: Type of artifact

        Raises:
            HubValidationError: If validation fails
        """
        try:
            # Validate required fields
            if self.config.require_version and not metadata.get("version"):
                raise HubValidationError("Version is required")
            if self.config.require_description and not metadata.get("description"):
                raise HubValidationError("Description is required")
            if self.config.require_author and not metadata.get("author"):
                raise HubValidationError("Author is required")

            # Validate visibility
            visibility = metadata.get("visibility", "private")
            if visibility not in self.config.allowed_visibilities:
                raise HubValidationError(f"Invalid visibility: {visibility}")

            # Validate with security manager
            storage_metadata = StorageMetadata(**metadata)
            await self.security.validate_artifact(
                artifact_type=artifact_type,
                content={},  # Empty content for metadata-only validation
                metadata=storage_metadata.dict(),
            )

        except HubValidationError:
            raise
        except Exception as e:
            raise HubValidationError(f"Metadata validation failed: {e}")

    async def get_artifact_type(self, artifact_id: str) -> str:
        """Get artifact type from storage.

        Args:
            artifact_id: ID of artifact

        Returns:
            str: Artifact type

        Raises:
            HubPublishingError: If type cannot be determined
        """
        try:
            # Try each known type until we find the artifact
            for artifact_type in ["agents", "workflows", "tools", "capabilities"]:
                try:
                    await self.storage.retrieve(
                        artifact_id=str(artifact_id),
                        artifact_type=artifact_type,
                    )
                    return artifact_type
                except Exception:
                    continue
            raise HubPublishingError(
                f"Could not determine type for artifact: {artifact_id}"
            )
        except Exception as e:
            raise HubPublishingError(f"Failed to get artifact type: {e}") from e

    async def publish(
        self,
        name: str,
        version: str,
        artifact_type: str,
        content: Dict[str, Any],
        description: str,
        author: str,
        tags: Set[str],
        visibility: str = "public",
    ) -> Tuple[str, str]:
        """Publish an artifact.

        Args:
            name: Artifact name
            version: Artifact version
            artifact_type: Type of artifact
            content: Artifact content
            description: Artifact description
            author: Artifact author
            tags: Set of tags
            visibility: Visibility level

        Returns:
            Tuple of (artifact_id, marketplace_id)

        Raises:
            HubPublishingError: If publishing fails
        """
        try:
            # Generate artifact ID
            artifact_id = str(uuid4())

            # Create metadata
            metadata = StorageMetadata(
                id=artifact_id,
                name=name,
                version=version,
                artifact_type=artifact_type,
                size=len(json.dumps(content)),
                hash=hashlib.sha256(json.dumps(content).encode()).hexdigest(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Validate metadata
            await self.validate_metadata(metadata.dict(), artifact_type)

            # Store artifact
            await self.storage.store(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                content=content,
                metadata=metadata,
            )

            # Publish to marketplace if public
            marketplace_id = ""
            if visibility == "public":
                marketplace_id = await self.marketplace.publish_artifact(
                    artifact_id=artifact_id,
                    artifact_type=artifact_type,
                    content=content,
                    metadata=metadata,
                    visibility=visibility,
                )

            return artifact_id, marketplace_id

        except Exception as e:
            raise HubPublishingError(
                f"Failed to publish artifact: {str(e)}",
                details={
                    "name": name,
                    "version": version,
                    "type": artifact_type,
                },
            )

    async def update(
        self,
        artifact_id: str,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        signature: Optional[str] = None,
    ) -> None:
        """Update an artifact.

        Args:
            artifact_id: ID of artifact to update
            content: New content (optional)
            metadata: New metadata (optional)
            signature: Content signature (optional)

        Raises:
            HubPublishingError: If update fails
        """
        try:
            # Get artifact type
            artifact_type = await self.get_artifact_type(artifact_id)

            # Retrieve existing artifact
            stored_content, stored_metadata = await self.storage.retrieve(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
            )

            # Update content if provided
            if content is not None:
                stored_content.update(content)

            # Update metadata if provided
            if metadata is not None:
                stored_metadata = StorageMetadata(**{
                    **stored_metadata.dict(),
                    **metadata,
                    "updated_at": datetime.utcnow(),
                })

            # Store updated artifact
            await self.storage.store(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                content=stored_content,
                metadata=stored_metadata,
            )

        except Exception as e:
            raise HubPublishingError(
                f"Failed to update artifact: {str(e)}",
                details={"artifact_id": artifact_id},
            )

    async def delete(self, artifact_id: str, user_id: str) -> None:
        """Delete an artifact.

        Args:
            artifact_id: ID of artifact to delete
            user_id: ID of user requesting deletion

        Raises:
            HubPublishingError: If deletion fails
        """
        try:
            # Check permissions
            if not await self.security.check_access(
                user_id=user_id,
                artifact_id=artifact_id,
                operation="delete",
            ):
                raise HubPublishingError(
                    "User does not have permission to delete artifact",
                    details={
                        "user_id": user_id,
                        "artifact_id": artifact_id,
                    },
                )

            # Get artifact type
            artifact_type = await self.get_artifact_type(artifact_id)

            # Delete from storage
            await self.storage.delete(
                artifact_id=str(artifact_id),
                artifact_type=artifact_type,
            )

            # Log deletion event
            await audit_logger.log({
                "event_type": "hub.delete",
                "artifact_id": artifact_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

        except Exception as e:
            raise HubPublishingError(f"Failed to delete artifact: {e}") from e
