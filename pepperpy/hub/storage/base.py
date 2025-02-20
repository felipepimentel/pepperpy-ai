"""Base storage module for the Pepperpy Hub.

This module defines the base storage interfaces and metadata types.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


class StorageMetadata(BaseModel):
    """Metadata for stored artifacts."""

    id: str = Field(..., description="Unique identifier for the artifact")
    name: str = Field(..., description="Name of the artifact")
    version: str = Field(..., description="Version of the artifact")
    artifact_type: str = Field(..., description="Type of the artifact")
    size: int = Field(..., description="Size of the artifact in bytes")
    hash: str = Field(..., description="Hash of the artifact content")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the artifact was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the artifact was last updated",
    )


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend.

        This method should be called before using the storage backend.
        It should set up any necessary resources or connections.

        Raises:
            PepperpyError: If initialization fails.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend.

        This method should be called when the storage backend is no longer needed.
        It should clean up any resources or connections.

        Raises:
            PepperpyError: If cleanup fails.
        """
        pass

    @abstractmethod
    async def store(
        self,
        artifact_id: str,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: StorageMetadata,
    ) -> None:
        """Store an artifact.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact (agent, workflow, tool, capability).
            content: Artifact content to store.
            metadata: Metadata about the artifact.

        Raises:
            PepperpyError: If storage fails.
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        artifact_id: str,
        artifact_type: str,
    ) -> Tuple[Dict[str, Any], StorageMetadata]:
        """Retrieve an artifact.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact (agent, workflow, tool, capability).

        Returns:
            Tuple of (content, metadata).

        Raises:
            PepperpyError: If retrieval fails or artifact doesn't exist.
        """
        pass

    @abstractmethod
    async def delete(self, artifact_id: str, artifact_type: str) -> None:
        """Delete an artifact.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact_type: Type of the artifact (agent, workflow, tool, capability).

        Raises:
            PepperpyError: If deletion fails or artifact doesn't exist.
        """
        pass

    @abstractmethod
    async def list(self) -> List[StorageMetadata]:
        """List all artifacts.

        Returns:
            List of metadata for all stored artifacts.

        Raises:
            PepperpyError: If listing fails.
        """
        pass
