"""Storage module for Hub artifacts.

This module provides storage backends for Hub artifacts.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from pepperpy.core.errors import StorageError
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class StorageMetadata(BaseModel):
    """Metadata for stored artifacts."""

    version: str
    type: str
    visibility: str = "public"
    extra: Dict[str, Any] = {}


class StorageBackend(ABC):
    """Base class for storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend."""
        pass

    @abstractmethod
    async def store(
        self,
        key: str,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: StorageMetadata,
    ) -> None:
        """Store an artifact.

        Args:
            key: Storage key
            artifact_type: Type of artifact
            content: Artifact content
            metadata: Artifact metadata
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        key: str,
        artifact_type: str,
    ) -> Dict[str, Any]:
        """Retrieve an artifact.

        Args:
            key: Storage key
            artifact_type: Type of artifact

        Returns:
            Dict[str, Any]: Artifact content
        """
        pass

    @abstractmethod
    async def delete(
        self,
        key: str,
        artifact_type: str,
    ) -> None:
        """Delete an artifact.

        Args:
            key: Storage key
            artifact_type: Type of artifact
        """
        pass

    @abstractmethod
    async def list(
        self,
        artifact_type: Optional[str] = None,
    ) -> Dict[str, StorageMetadata]:
        """List stored artifacts.

        Args:
            artifact_type: Optional type filter

        Returns:
            Dict[str, StorageMetadata]: Map of storage keys to metadata
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, root_dir: Path) -> None:
        """Initialize local storage.

        Args:
            root_dir: Root directory for storage
        """
        self.root_dir = root_dir
        self.artifacts_dir = root_dir / "artifacts"
        self.metadata_dir = root_dir / "metadata"

    async def initialize(self) -> None:
        """Initialize local storage."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """Close local storage."""
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
        """
        # Store artifact content
        artifact_path = self.artifacts_dir / f"{key}.json"
        artifact_path.write_text(json.dumps(content, indent=2))

        # Store metadata
        metadata_path = self.metadata_dir / f"{key}.json"
        metadata_path.write_text(metadata.model_dump_json(indent=2))

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
        """
        artifact_path = self.artifacts_dir / f"{key}.json"
        if not artifact_path.exists():
            raise KeyError(f"Artifact not found: {key}")

        return json.loads(artifact_path.read_text())

    async def delete(
        self,
        key: str,
        artifact_type: str,
    ) -> None:
        """Delete an artifact from local storage.

        Args:
            key: Storage key
            artifact_type: Type of artifact
        """
        # Delete artifact content
        artifact_path = self.artifacts_dir / f"{key}.json"
        if artifact_path.exists():
            artifact_path.unlink()

        # Delete metadata
        metadata_path = self.metadata_dir / f"{key}.json"
        if metadata_path.exists():
            metadata_path.unlink()

    async def list(
        self,
        artifact_type: Optional[str] = None,
    ) -> Dict[str, StorageMetadata]:
        """List artifacts in local storage.

        Args:
            artifact_type: Optional type filter

        Returns:
            Dict[str, StorageMetadata]: Map of storage keys to metadata
        """
        results = {}
        for metadata_path in self.metadata_dir.glob("*.json"):
            metadata = StorageMetadata.model_validate_json(metadata_path.read_text())
            if not artifact_type or metadata.type == artifact_type:
                key = metadata_path.stem
                results[key] = metadata
        return results
