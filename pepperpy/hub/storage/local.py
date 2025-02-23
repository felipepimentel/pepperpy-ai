"""Local storage backend for Hub artifacts.

This module provides a local filesystem storage backend for Hub artifacts.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy.core.errors import StorageError
from pepperpy.hub.storage.base import StorageBackend, StorageMetadata
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend.

    This backend stores artifacts and metadata in the local filesystem:
    - Artifacts are stored as JSON files in the artifacts directory
    - Metadata is stored as JSON files in the metadata directory
    """

    def __init__(self, root_dir: Path) -> None:
        """Initialize local storage.

        Args:
            root_dir: Root directory for storage
        """
        self.root_dir = root_dir
        self.artifacts_dir = root_dir / "artifacts"
        self.metadata_dir = root_dir / "metadata"

    async def initialize(self) -> None:
        """Initialize local storage.

        Creates the required directories if they don't exist.
        """
        try:
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Local storage initialized", extra={"path": str(self.root_dir)})
        except Exception as e:
            raise StorageError(f"Failed to initialize local storage: {e}")

    async def close(self) -> None:
        """Close local storage.

        No cleanup needed for local storage.
        """
        pass

    async def store(
        self,
        key: str,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: StorageMetadata,
    ) -> None:
        """Store an artifact locally.

        Args:
            key: Storage key
            artifact_type: Type of artifact
            content: Artifact content
            metadata: Artifact metadata

        Raises:
            StorageError: If storage fails
        """
        try:
            # Store artifact content
            artifact_path = self.artifacts_dir / f"{key}.json"
            artifact_path.write_text(json.dumps(content, indent=2))

            # Store metadata
            metadata_path = self.metadata_dir / f"{key}.json"
            metadata_path.write_text(metadata.model_dump_json(indent=2))

            logger.info(
                "Stored artifact",
                extra={
                    "key": key,
                    "type": artifact_type,
                    "size": len(json.dumps(content)),
                },
            )
        except Exception as e:
            raise StorageError(f"Failed to store artifact {key}: {e}")

    async def retrieve(
        self,
        key: str,
        artifact_type: str,
    ) -> Dict[str, Any]:
        """Retrieve an artifact from local storage.

        Args:
            key: Storage key
            artifact_type: Type of artifact

        Returns:
            Dict[str, Any]: Artifact content

        Raises:
            KeyError: If artifact not found
            StorageError: If retrieval fails
        """
        try:
            artifact_path = self.artifacts_dir / f"{key}.json"
            if not artifact_path.exists():
                raise KeyError(f"Artifact not found: {key}")

            content = json.loads(artifact_path.read_text())
            logger.info(
                "Retrieved artifact",
                extra={
                    "key": key,
                    "type": artifact_type,
                    "size": len(json.dumps(content)),
                },
            )
            return content

        except KeyError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to retrieve artifact {key}: {e}")

    async def delete(
        self,
        key: str,
        artifact_type: str,
    ) -> None:
        """Delete an artifact from local storage.

        Args:
            key: Storage key
            artifact_type: Type of artifact

        Raises:
            KeyError: If artifact not found
            StorageError: If deletion fails
        """
        try:
            # Delete artifact content
            artifact_path = self.artifacts_dir / f"{key}.json"
            if not artifact_path.exists():
                raise KeyError(f"Artifact not found: {key}")

            artifact_path.unlink()

            # Delete metadata
            metadata_path = self.metadata_dir / f"{key}.json"
            if metadata_path.exists():
                metadata_path.unlink()

            logger.info("Deleted artifact", extra={"key": key, "type": artifact_type})

        except KeyError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete artifact {key}: {e}")

    async def list(
        self,
        artifact_type: Optional[str] = None,
    ) -> Dict[str, StorageMetadata]:
        """List artifacts in local storage.

        Args:
            artifact_type: Optional type filter

        Returns:
            Dict[str, StorageMetadata]: Map of storage keys to metadata

        Raises:
            StorageError: If listing fails
        """
        try:
            results = {}
            for metadata_path in self.metadata_dir.glob("*.json"):
                try:
                    metadata = StorageMetadata.model_validate_json(
                        metadata_path.read_text()
                    )
                    if not artifact_type or metadata.type == artifact_type:
                        key = metadata_path.stem
                        results[key] = metadata
                except Exception as e:
                    logger.warning(
                        f"Failed to load metadata from {metadata_path}: {e}",
                        exc_info=True,
                    )

            logger.info(
                "Listed artifacts",
                extra={"count": len(results), "type_filter": artifact_type},
            )
            return results

        except Exception as e:
            raise StorageError(f"Failed to list artifacts: {e}")
