"""Local storage backend for the Pepperpy Hub.

This module provides a local file system implementation of the storage backend.
It stores artifacts in a structured directory hierarchy under the user's home directory.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.core.errors import PepperpyError
from pepperpy.hub.storage.base import StorageBackend, StorageMetadata
from pepperpy.monitoring import logger


class LocalStorageBackend(StorageBackend):
    """Local file system implementation of the storage backend."""

    def __init__(self, root_dir: Optional[str] = None) -> None:
        """Initialize the local storage backend.

        Args:
            root_dir: Optional root directory for storage. If not provided,
                defaults to ~/.pepperpy/hub/storage.
        """
        self.root_dir = (
            Path(root_dir) if root_dir else Path.home() / ".pepperpy/hub/storage"
        )
        self.root_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized local storage at {self.root_dir}")

    async def initialize(self) -> None:
        """Initialize the storage backend.

        Creates necessary directories if they don't exist.
        """
        try:
            # Create type-specific directories
            for artifact_type in ["agent", "workflow", "tool", "capability"]:
                type_dir = self.root_dir / artifact_type
                type_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Initialized local storage directories")

        except Exception as e:
            raise PepperpyError(
                f"Failed to initialize local storage: {str(e)}",
                recovery_hint="Check if you have write permissions in the storage directory",
            )

    async def close(self) -> None:
        """Close the storage backend.

        No cleanup needed for local storage.
        """
        pass

    async def store(
        self,
        artifact_id: str,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: StorageMetadata,
    ) -> None:
        """Store an artifact in the local file system.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact (agent, workflow, tool, capability).
            content: Artifact content to store.
            metadata: Metadata about the artifact.

        Raises:
            PepperpyError: If storage fails.
        """
        try:
            # Validate artifact type
            if artifact_type not in ["agent", "workflow", "tool", "capability"]:
                raise ValueError(f"Invalid artifact type: {artifact_type}")

            # Create artifact directory
            artifact_dir = self.root_dir / artifact_type / artifact_id
            artifact_dir.mkdir(parents=True, exist_ok=True)

            # Store content
            content_file = artifact_dir / "content.json"
            with open(content_file, "w") as f:
                json.dump(content, f, indent=2)

            # Store metadata
            metadata_file = artifact_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata.dict(), f, indent=2)

            logger.debug(f"Stored artifact {artifact_id} in {artifact_dir}")

        except Exception as e:
            raise PepperpyError(
                f"Failed to store artifact {artifact_id}: {str(e)}",
                recovery_hint="Check if you have write permissions and sufficient disk space",
            )

    async def retrieve(
        self,
        artifact_id: str,
        artifact_type: str,
    ) -> tuple[Dict[str, Any], StorageMetadata]:
        """Retrieve an artifact from the local file system.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact (agent, workflow, tool, capability).

        Returns:
            Tuple of (content, metadata).

        Raises:
            PepperpyError: If retrieval fails or artifact doesn't exist.
        """
        try:
            # Validate artifact type
            if artifact_type not in ["agent", "workflow", "tool", "capability"]:
                raise ValueError(f"Invalid artifact type: {artifact_type}")

            # Get artifact directory
            artifact_dir = self.root_dir / artifact_type / artifact_id
            if not artifact_dir.exists():
                raise FileNotFoundError(f"Artifact {artifact_id} not found")

            # Load content
            content_file = artifact_dir / "content.json"
            with open(content_file) as f:
                content = json.load(f)

            # Load metadata
            metadata_file = artifact_dir / "metadata.json"
            with open(metadata_file) as f:
                metadata_dict = json.load(f)
                metadata = StorageMetadata(**metadata_dict)

            logger.debug(f"Retrieved artifact {artifact_id} from {artifact_dir}")
            return content, metadata

        except FileNotFoundError:
            raise PepperpyError(
                f"Artifact {artifact_id} not found",
                recovery_hint="Check if the artifact ID and type are correct",
            )
        except Exception as e:
            raise PepperpyError(
                f"Failed to retrieve artifact {artifact_id}: {str(e)}",
                recovery_hint="Check if you have read permissions and the storage is not corrupted",
            )

    async def delete(self, artifact_id: str, artifact_type: str) -> None:
        """Delete an artifact from the local file system.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact (agent, workflow, tool, capability).

        Raises:
            PepperpyError: If deletion fails or artifact doesn't exist.
        """
        try:
            # Validate artifact type
            if artifact_type not in ["agent", "workflow", "tool", "capability"]:
                raise ValueError(f"Invalid artifact type: {artifact_type}")

            # Get artifact directory
            artifact_dir = self.root_dir / artifact_type / artifact_id
            if not artifact_dir.exists():
                raise FileNotFoundError(f"Artifact {artifact_id} not found")

            # Delete directory
            shutil.rmtree(artifact_dir)
            logger.debug(f"Deleted artifact {artifact_id} from {artifact_dir}")

        except FileNotFoundError:
            raise PepperpyError(
                f"Artifact {artifact_id} not found",
                recovery_hint="Check if the artifact ID and type are correct",
            )
        except Exception as e:
            raise PepperpyError(
                f"Failed to delete artifact {artifact_id}: {str(e)}",
                recovery_hint="Check if you have write permissions",
            )

    async def list(self) -> List[StorageMetadata]:
        """List all artifacts in the local storage.

        Returns:
            List of metadata for all stored artifacts.

        Raises:
            PepperpyError: If listing fails.
        """
        try:
            artifacts = []
            # List artifacts in each type directory
            for artifact_type in ["agent", "workflow", "tool", "capability"]:
                type_dir = self.root_dir / artifact_type
                if not type_dir.exists():
                    continue

                # Get metadata for each artifact
                for artifact_dir in type_dir.iterdir():
                    if not artifact_dir.is_dir():
                        continue

                    metadata_file = artifact_dir / "metadata.json"
                    if not metadata_file.exists():
                        continue

                    with open(metadata_file) as f:
                        metadata_dict = json.load(f)
                        artifacts.append(StorageMetadata(**metadata_dict))

            logger.debug(f"Listed {len(artifacts)} artifacts from local storage")
            return artifacts

        except Exception as e:
            raise PepperpyError(
                f"Failed to list artifacts: {str(e)}",
                recovery_hint="Check if you have read permissions",
            )
