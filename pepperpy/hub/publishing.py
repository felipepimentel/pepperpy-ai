"""Publishing module for the Pepperpy Hub.

This module provides functionality for publishing artifacts to the Hub,
including validation, versioning, and metadata management.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, Set, Tuple

from pydantic import BaseModel, Field

from pepperpy.core.errors import PepperpyError
from pepperpy.hub.marketplace import MarketplaceManager
from pepperpy.hub.security import SecurityManager
from pepperpy.hub.storage import StorageBackend, StorageMetadata
from pepperpy.monitoring import logger


class PublishConfig(BaseModel):
    """Configuration for artifact publishing."""

    require_signature: bool = Field(
        default=False,
        description="Whether to require cryptographic signatures",
    )
    require_description: bool = Field(
        default=True,
        description="Whether to require artifact descriptions",
    )
    require_author: bool = Field(
        default=True,
        description="Whether to require author information",
    )
    require_version: bool = Field(
        default=True,
        description="Whether to require version information",
    )
    allowed_visibilities: Set[str] = Field(
        default={"public", "private", "shared"},
        description="Allowed visibility levels",
    )


class Publisher:
    """Manager for artifact publishing."""

    def __init__(
        self,
        storage: StorageBackend,
        security: SecurityManager,
        marketplace: MarketplaceManager,
        config: Optional[PublishConfig] = None,
    ) -> None:
        """Initialize the publisher.

        Args:
            storage: Storage backend for artifacts.
            security: Security manager for validation.
            marketplace: Marketplace manager for publishing.
            config: Optional publishing configuration.
        """
        self.storage = storage
        self.security = security
        self.marketplace = marketplace
        self.config = config or PublishConfig()
        logger.debug("Initialized publisher")

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
            name: Name of the artifact.
            version: Version of the artifact.
            artifact_type: Type of the artifact.
            content: Artifact content.
            description: Description of the artifact.
            author: Author of the artifact.
            tags: Tags for the artifact.
            visibility: Visibility level (public, private, shared).

        Returns:
            Tuple of (artifact_id, marketplace_id).

        Raises:
            PepperpyError: If publishing fails.
        """
        try:
            # Validate inputs
            if not name:
                raise ValueError("Name is required")
            if self.config.require_version and not version:
                raise ValueError("Version is required")
            if self.config.require_description and not description:
                raise ValueError("Description is required")
            if self.config.require_author and not author:
                raise ValueError("Author is required")
            if visibility not in self.config.allowed_visibilities:
                raise ValueError(f"Invalid visibility: {visibility}")

            # Create metadata
            metadata = StorageMetadata(
                id=f"{name}_{version}",
                name=name,
                version=version,
                artifact_type=artifact_type,
                size=len(str(content).encode()),
                hash=hashlib.sha256(str(content).encode()).hexdigest(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Validate artifact
            await self.security.validate_artifact(
                artifact_type=artifact_type,
                content=content,
                metadata=metadata.dict(),
            )

            # Store artifact locally
            await self.storage.store(
                artifact_id=metadata.id,
                artifact_type=artifact_type,
                content=content,
                metadata=metadata,
            )

            # Publish to marketplace
            marketplace_id = await self.marketplace.publish_artifact(
                artifact_id=metadata.id,
                artifact_type=artifact_type,
                content=content,
                metadata=metadata,
                visibility=visibility,
            )

            logger.info(f"Published artifact {name}@{version}")
            return metadata.id, marketplace_id

        except Exception as e:
            raise PepperpyError(
                f"Failed to publish artifact {name}@{version}: {str(e)}",
                recovery_hint="Check if all required fields are provided and valid",
            )

    async def update(
        self,
        artifact_id: str,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        signature: Optional[str] = None,
    ) -> None:
        """Update an existing artifact.

        Args:
            artifact_id: Artifact to update
            content: Optional new content
            metadata: Optional new metadata
            signature: Optional new signature

        Raises:
            HubPublishingError: If update fails
        """
        try:
            # Load existing artifact
            artifact = await self.storage.load(artifact_id)

            # Update fields
            if content is not None:
                artifact.content = content
            if metadata is not None:
                artifact.metadata.update(metadata)
            if signature is not None:
                artifact.signature = signature

            # Validate updated artifact
            await self.security.validate_artifact(
                artifact_type=artifact.artifact_type,
                content=artifact.content,
                metadata=artifact.metadata,
            )

            # Save updated artifact
            await self.storage.save(artifact)

            # Log update event
            await audit_logger.log({
                "event_type": "hub.update",
                "artifact_id": artifact_id,
                "timestamp": datetime.utcnow(),
            })

        except Exception as e:
            raise HubPublishingError(f"Failed to update artifact: {e}") from e

    async def delete(self, artifact_id: str, user_id: str) -> None:
        """Delete an artifact.

        Args:
            artifact_id: Artifact to delete
            user_id: User requesting deletion

        Raises:
            HubPublishingError: If deletion fails
        """
        try:
            # Check access
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

            # Delete from storage
            await self.storage.delete(artifact_id)

            # Log deletion event
            await audit_logger.log({
                "event_type": "hub.delete",
                "artifact_id": artifact_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
            })

        except Exception as e:
            raise HubPublishingError(f"Failed to delete artifact: {e}") from e

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
            # Check required fields
            required_fields = {
                "name",
                "version",
                "description",
                "author",
            }
            missing_fields = required_fields - set(metadata.keys())
            if missing_fields:
                raise HubValidationError(
                    "Missing required metadata fields",
                    details={
                        "missing_fields": list(missing_fields),
                    },
                )

            # Check version format
            version = metadata["version"]
            if not isinstance(version, str):
                raise HubValidationError(
                    "Version must be a string",
                    details={"version": version},
                )

            # Check name format
            name = metadata["name"]
            if not isinstance(name, str) or not name:
                raise HubValidationError(
                    "Name must be a non-empty string",
                    details={"name": name},
                )

            # Check description
            description = metadata["description"]
            if not isinstance(description, str) or not description:
                raise HubValidationError(
                    "Description must be a non-empty string",
                    details={"description": description},
                )

            # Check author
            author = metadata["author"]
            if not isinstance(author, str) or not author:
                raise HubValidationError(
                    "Author must be a non-empty string",
                    details={"author": author},
                )

            # Log validation event
            await audit_logger.log({
                "event_type": "hub.validate_metadata",
                "artifact_type": artifact_type,
                "timestamp": datetime.utcnow(),
            })

        except HubValidationError:
            raise
        except Exception as e:
            raise HubValidationError(f"Metadata validation failed: {e}") from e
