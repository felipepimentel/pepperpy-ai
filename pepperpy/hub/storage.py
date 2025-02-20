"""Storage abstraction for the Pepperpy Hub.

This module provides the storage interface and implementations for:
- Local file system storage
- Remote storage (e.g., S3, GCS)
- Hybrid storage with caching
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

    id: UUID
    name: str
    version: str
    type: str
    size: int
    hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def init(self) -> None:
        """Initialize the storage backend."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend."""
        pass

    @abstractmethod
    async def store(
        self,
        artifact_id: UUID,
        artifact_type: str,
        data: Union[str, bytes, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageMetadata:
        """Store an artifact.

        Args:
            artifact_id: Unique identifier for the artifact
            artifact_type: Type of artifact (agent, workflow, tool, capability)
            data: Artifact data to store
            metadata: Optional metadata for the artifact

        Returns:
            StorageMetadata: Metadata for the stored artifact

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        artifact_id: UUID,
        artifact_type: str,
    ) -> Dict[str, Any]:
        """Retrieve an artifact.

        Args:
            artifact_id: ID of the artifact to retrieve
            artifact_type: Type of artifact

        Returns:
            Dict[str, Any]: Retrieved artifact data

        Raises:
            StorageError: If retrieval fails
        """
        pass

    @abstractmethod
    async def delete(
        self,
        artifact_id: UUID,
        artifact_type: str,
    ) -> None:
        """Delete an artifact.

        Args:
            artifact_id: ID of the artifact to delete
            artifact_type: Type of artifact

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def list(
        self,
        artifact_type: Optional[str] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[StorageMetadata]:
        """List stored artifacts.

        Args:
            artifact_type: Optional type to filter by
            filter_criteria: Optional filtering criteria

        Returns:
            List[StorageMetadata]: List of artifact metadata

        Raises:
            StorageError: If listing fails
        """
        pass

    @abstractmethod
    async def get_metadata(
        self,
        artifact_id: UUID,
        artifact_type: str,
    ) -> StorageMetadata:
        """Get artifact metadata.

        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of artifact

        Returns:
            StorageMetadata: Artifact metadata

        Raises:
            StorageError: If metadata retrieval fails
        """
        pass

    @abstractmethod
    async def update_metadata(
        self,
        artifact_id: UUID,
        artifact_type: str,
        metadata: Dict[str, Any],
    ) -> StorageMetadata:
        """Update artifact metadata.

        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of artifact
            metadata: New metadata to update

        Returns:
            StorageMetadata: Updated artifact metadata

        Raises:
            StorageError: If metadata update fails
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local file system storage backend."""

    def __init__(self, root_dir: Optional[Union[str, Path]] = None) -> None:
        """Initialize local storage.

        Args:
            root_dir: Optional root directory for storage.
                     Defaults to ~/.pepperpy/hub/storage
        """
        if root_dir is None:
            root_dir = Path.home() / ".pepperpy" / "hub" / "storage"
        self.root_dir = Path(root_dir)
        self._lock = asyncio.Lock()
        self._metadata: Dict[str, Dict[UUID, StorageMetadata]] = {}

    async def init(self) -> None:
        """Initialize local storage."""
        # Create storage directories
        self.root_dir.mkdir(parents=True, exist_ok=True)
        for artifact_type in ["agents", "workflows", "tools", "capabilities"]:
            (self.root_dir / artifact_type).mkdir(exist_ok=True)

        # Load existing metadata
        async with self._lock:
            for artifact_type in ["agents", "workflows", "tools", "capabilities"]:
                self._metadata[artifact_type] = {}
                type_dir = self.root_dir / artifact_type
                for meta_file in type_dir.glob("*.meta.json"):
                    try:
                        with open(meta_file, "r") as f:
                            meta_data = json.load(f)
                            metadata = StorageMetadata(**meta_data)
                            self._metadata[artifact_type][metadata.id] = metadata
                    except Exception as e:
                        logger.error(f"Failed to load metadata from {meta_file}: {e}")

    async def close(self) -> None:
        """Close local storage."""
        # Nothing to do for local storage
        pass

    async def store(
        self,
        artifact_id: UUID,
        artifact_type: str,
        data: Union[str, bytes, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageMetadata:
        """Store an artifact in local storage."""
        type_dir = self.root_dir / artifact_type
        artifact_file = type_dir / f"{artifact_id}.json"
        meta_file = type_dir / f"{artifact_id}.meta.json"

        try:
            # Write artifact data
            if isinstance(data, bytes):
                content = data.decode("utf-8")
            elif isinstance(data, dict):
                content = json.dumps(data, indent=2)
            else:
                content = str(data)

            async with self._lock:
                with open(artifact_file, "w") as f:
                    f.write(content)

                # Create and store metadata
                storage_meta = StorageMetadata(
                    id=artifact_id,
                    name=str(artifact_id),
                    version="1.0.0",  # TODO: Get from data
                    type=artifact_type,
                    size=len(content),
                    hash="",  # TODO: Calculate hash
                    metadata=metadata or {},
                )

                with open(meta_file, "w") as f:
                    json.dump(storage_meta.dict(), f, indent=2, default=str)

                self._metadata.setdefault(artifact_type, {})[artifact_id] = storage_meta
                return storage_meta

        except Exception as e:
            raise StorageError(f"Failed to store artifact: {e}") from e

    async def retrieve(
        self,
        artifact_id: UUID,
        artifact_type: str,
    ) -> Dict[str, Any]:
        """Retrieve an artifact from local storage."""
        artifact_file = self.root_dir / artifact_type / f"{artifact_id}.json"

        try:
            with open(artifact_file, "r") as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"Failed to retrieve artifact: {e}") from e

    async def delete(
        self,
        artifact_id: UUID,
        artifact_type: str,
    ) -> None:
        """Delete an artifact from local storage."""
        artifact_file = self.root_dir / artifact_type / f"{artifact_id}.json"
        meta_file = self.root_dir / artifact_type / f"{artifact_id}.meta.json"

        try:
            async with self._lock:
                if artifact_file.exists():
                    artifact_file.unlink()
                if meta_file.exists():
                    meta_file.unlink()
                if artifact_type in self._metadata:
                    self._metadata[artifact_type].pop(artifact_id, None)
        except Exception as e:
            raise StorageError(f"Failed to delete artifact: {e}") from e

    async def list(
        self,
        artifact_type: Optional[str] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[StorageMetadata]:
        """List artifacts in local storage."""
        try:
            async with self._lock:
                if artifact_type:
                    if artifact_type not in self._metadata:
                        return []
                    metadata_list = list(self._metadata[artifact_type].values())
                else:
                    metadata_list = []
                    for type_meta in self._metadata.values():
                        metadata_list.extend(type_meta.values())

                if filter_criteria:
                    filtered_list = []
                    for meta in metadata_list:
                        if all(
                            meta.metadata.get(k) == v
                            for k, v in filter_criteria.items()
                        ):
                            filtered_list.append(meta)
                    return filtered_list

                return metadata_list
        except Exception as e:
            raise StorageError(f"Failed to list artifacts: {e}") from e

    async def get_metadata(
        self,
        artifact_id: UUID,
        artifact_type: str,
    ) -> StorageMetadata:
        """Get artifact metadata from local storage."""
        try:
            async with self._lock:
                if (
                    artifact_type not in self._metadata
                    or artifact_id not in self._metadata[artifact_type]
                ):
                    raise StorageError(f"Artifact not found: {artifact_id}")
                return self._metadata[artifact_type][artifact_id]
        except Exception as e:
            raise StorageError(f"Failed to get metadata: {e}") from e

    async def update_metadata(
        self,
        artifact_id: UUID,
        artifact_type: str,
        metadata: Dict[str, Any],
    ) -> StorageMetadata:
        """Update artifact metadata in local storage."""
        meta_file = self.root_dir / artifact_type / f"{artifact_id}.meta.json"

        try:
            async with self._lock:
                if (
                    artifact_type not in self._metadata
                    or artifact_id not in self._metadata[artifact_type]
                ):
                    raise StorageError(f"Artifact not found: {artifact_id}")

                # Update metadata
                storage_meta = self._metadata[artifact_type][artifact_id]
                storage_meta.metadata.update(metadata)
                storage_meta.updated_at = datetime.utcnow()

                # Save to file
                with open(meta_file, "w") as f:
                    json.dump(storage_meta.dict(), f, indent=2, default=str)

                return storage_meta
        except Exception as e:
            raise StorageError(f"Failed to update metadata: {e}") from e
