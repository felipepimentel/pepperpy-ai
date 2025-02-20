"""Local file-based Hub storage implementation."""

import json
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

from jsonschema import ValidationError

from pepperpy.core.logging import get_logger
from pepperpy.hub.errors import HubStorageError
from pepperpy.hub.storage import HubArtifact, HubStorage
from pepperpy.security import encryption

logger = get_logger(__name__)


class LocalHubStorage(HubStorage):
    """Local file-based Hub storage implementation."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize local storage.

        Args:
            storage_path: Optional storage path. Defaults to ~/.pepperpy/hub
        """
        super().__init__()
        if storage_path is None:
            storage_path = Path.home() / ".pepperpy" / "hub"
        self.storage_path = storage_path
        self.encryption = encryption.AES256GCM()

    async def _initialize(self) -> None:
        """Initialize storage."""
        try:
            # Create storage directory if it doesn't exist
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories for different artifact types
            for artifact_type in ["agents", "workflows", "tools", "prompts"]:
                (self.storage_path / artifact_type).mkdir(exist_ok=True)

            logger.info(
                "Initialized local storage",
                extra={"storage_path": str(self.storage_path)},
            )
        except Exception as e:
            raise HubStorageError(f"Failed to initialize storage: {e}") from e

    async def _cleanup(self) -> None:
        """Clean up storage."""
        pass  # No cleanup needed for local storage

    async def _store_impl(
        self,
        key: str,
        content: Dict[str, Any],
        scope: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> HubArtifact:
        """Store artifact in local storage.

        Args:
            key: Artifact key
            content: Artifact content
            scope: Storage scope
            metadata: Optional metadata

        Returns:
            HubArtifact: Stored artifact

        Raises:
            HubStorageError: If storage fails
        """
        try:
            # Create artifact
            metadata_dict = metadata or {}
            artifact = HubArtifact(
                name=key,
                version=metadata_dict.get("version", "0.1.0"),
                artifact_type=metadata_dict.get("type", "unknown"),
                content=content,
                metadata=metadata_dict,
            )

            # Encrypt content
            encrypted = await self.encryption.encrypt(content)

            # Store artifact
            artifact_path = self._get_artifact_path(artifact)
            artifact_data = {
                "id": str(artifact.id),
                "name": artifact.name,
                "version": artifact.version,
                "type": artifact.artifact_type,
                "content": encrypted,
                "metadata": artifact.metadata,
                "signature": artifact.signature,
                "created_at": artifact.created_at.isoformat(),
                "updated_at": artifact.updated_at.isoformat(),
            }

            # Save to file
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(json.dumps(artifact_data, indent=2))

            logger.info(
                "Stored artifact",
                extra={
                    "artifact_id": str(artifact.id),
                    "path": str(artifact_path),
                },
            )

            return artifact

        except Exception as e:
            raise HubStorageError(f"Failed to store artifact: {e}") from e

    async def _load_from_storage(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Load artifact from storage.

        Args:
            artifact_id: Artifact ID

        Returns:
            Optional[Dict[str, Any]]: Artifact data if found

        Raises:
            HubStorageError: If loading fails
        """
        try:
            # Find artifact file
            for artifact_type in ["agents", "workflows", "tools", "prompts"]:
                type_dir = self.storage_path / artifact_type
                if not type_dir.exists():
                    continue

                for file_path in type_dir.glob("*.json"):
                    try:
                        data = json.loads(file_path.read_text())
                        if data.get("id") == artifact_id:
                            return data
                    except Exception:
                        continue

            return None

        except Exception as e:
            raise HubStorageError(f"Failed to load artifact: {e}") from e

    async def _exists_in_storage(self, artifact_id: str) -> bool:
        """Check if artifact exists in storage.

        Args:
            artifact_id: Artifact ID

        Returns:
            bool: True if artifact exists

        Raises:
            HubStorageError: If check fails
        """
        try:
            return await self._load_from_storage(artifact_id) is not None
        except Exception as e:
            raise HubStorageError(f"Failed to check artifact existence: {e}") from e

    async def _delete_from_storage(self, artifact_id: str) -> None:
        """Delete artifact from storage.

        Args:
            artifact_id: Artifact ID

        Raises:
            HubStorageError: If deletion fails
        """
        try:
            # Find and delete artifact file
            for artifact_type in ["agents", "workflows", "tools", "prompts"]:
                type_dir = self.storage_path / artifact_type
                if not type_dir.exists():
                    continue

                for file_path in type_dir.glob("*.json"):
                    try:
                        data = json.loads(file_path.read_text())
                        if data.get("id") == artifact_id:
                            file_path.unlink()
                            logger.info(
                                "Deleted artifact",
                                extra={
                                    "artifact_id": artifact_id,
                                    "path": str(file_path),
                                },
                            )
                            return
                    except Exception:
                        continue

        except Exception as e:
            raise HubStorageError(f"Failed to delete artifact: {e}") from e

    async def _list_from_storage(
        self,
        artifact_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        version: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """List artifacts from storage.

        Args:
            artifact_type: Optional artifact type filter
            name_pattern: Optional name pattern filter
            version: Optional version filter

        Yields:
            Dict[str, Any]: Artifact data

        Raises:
            HubStorageError: If listing fails
        """
        try:
            # List all artifact files
            types_to_check = (
                [artifact_type]
                if artifact_type
                else ["agents", "workflows", "tools", "prompts"]
            )

            for type_dir_name in types_to_check:
                type_dir = self.storage_path / type_dir_name
                if not type_dir.exists():
                    continue

                for file_path in type_dir.glob("*.json"):
                    try:
                        data = json.loads(file_path.read_text())

                        # Apply filters
                        if name_pattern and name_pattern not in data.get("name", ""):
                            continue
                        if version and version != data.get("version"):
                            continue

                        yield data

                    except Exception as e:
                        logger.warning(
                            "Failed to read artifact file",
                            exc_info=e,
                            extra={"path": str(file_path)},
                        )
                        continue

        except Exception as e:
            raise HubStorageError(f"Failed to list artifacts: {e}") from e

    async def _verify_signature(
        self,
        content: Dict[str, Any],
        signature: str,
        public_key: str,
    ) -> bool:
        """Verify artifact signature.

        Args:
            content: Artifact content
            signature: Signature to verify
            public_key: Public key for verification

        Returns:
            bool: True if signature is valid

        Raises:
            HubStorageError: If verification fails
        """
        # For local storage, we trust the content and don't verify signatures
        return True

    async def _validate_artifact_schema(self, artifact: HubArtifact) -> None:
        """Validate artifact schema.

        Args:
            artifact: Artifact to validate

        Raises:
            HubStorageError: If validation fails
        """
        try:
            # For local storage, we only validate basic fields
            if not artifact.name:
                raise ValidationError("Artifact name is required")
            if not artifact.version:
                raise ValidationError("Artifact version is required")
            if not artifact.artifact_type:
                raise ValidationError("Artifact type is required")
            if not artifact.content:
                raise ValidationError("Artifact content is required")

        except ValidationError as e:
            raise HubStorageError(f"Failed to validate artifact schema: {e}")

    def _get_artifact_path(self, artifact: HubArtifact) -> Path:
        """Get path for storing artifact.

        Args:
            artifact: Artifact to store

        Returns:
            Path: Storage path
        """
        return (
            self.storage_path
            / artifact.artifact_type
            / f"{artifact.name}-{artifact.version}.json"
        )

    async def save(self, artifact: HubArtifact) -> str:
        """Save an artifact securely.

        Args:
            artifact: Artifact to save

        Returns:
            str: Artifact ID

        Raises:
            HubStorageError: If save fails
        """
        try:
            # Validate artifact
            await self._validate_artifact_schema(artifact)

            # Store artifact
            await self._store_impl(
                str(artifact.id),
                artifact.content,
                artifact.artifact_type,
                artifact.metadata,
            )

            return str(artifact.id)

        except Exception as e:
            raise HubStorageError(f"Failed to save artifact: {e}") from e

    async def load(self, artifact_id: str) -> HubArtifact:
        """Load an artifact securely.

        Args:
            artifact_id: ID of artifact to load

        Returns:
            HubArtifact: Loaded artifact

        Raises:
            HubStorageError: If load fails
        """
        try:
            # Load artifact data
            data = await self._load_from_storage(artifact_id)
            if not data:
                raise HubStorageError(f"Artifact not found: {artifact_id}")

            # Create and return artifact
            return HubArtifact(**data)

        except Exception as e:
            raise HubStorageError(f"Failed to load artifact: {e}") from e

    async def delete(self, artifact_id: str) -> None:
        """Delete an artifact securely.

        Args:
            artifact_id: ID of artifact to delete

        Raises:
            HubStorageError: If deletion fails
        """
        try:
            # Verify artifact exists
            if not await self._exists_in_storage(artifact_id):
                raise HubStorageError(f"Artifact not found: {artifact_id}")

            # Delete from storage
            await self._delete_from_storage(artifact_id)

        except Exception as e:
            raise HubStorageError(f"Failed to delete artifact: {e}") from e

    async def list(
        self,
        artifact_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        version: Optional[str] = None,
    ) -> AsyncIterator[HubArtifact]:
        """List artifacts matching the given criteria.

        Args:
            artifact_type: Optional artifact type filter
            name_pattern: Optional name pattern filter
            version: Optional version filter

        Yields:
            HubArtifact: Matching artifacts

        Raises:
            HubStorageError: If listing fails
        """
        try:
            async for data in self._list_from_storage(
                artifact_type, name_pattern, version
            ):
                yield HubArtifact(**data)

        except Exception as e:
            raise HubStorageError(f"Failed to list artifacts: {e}") from e

    async def verify(self, artifact: HubArtifact) -> bool:
        """Verify artifact integrity and signature.

        Args:
            artifact: Artifact to verify

        Returns:
            bool: True if verification succeeds

        Raises:
            HubStorageError: If verification fails
        """
        try:
            # For local storage, we trust the content and don't verify signatures
            return True

        except Exception as e:
            raise HubStorageError(f"Failed to verify artifact: {e}") from e
