"""Storage module for Hub artifacts.

This module provides storage backends for Hub artifacts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class StorageMetadata(BaseModel):
    """Metadata for stored artifacts.

    Attributes:
        version: Version of the artifact
        type: Type of artifact (e.g. "agent", "workflow")
        visibility: Visibility level ("public", "private", "shared")
        extra: Additional metadata fields
    """

    version: str
    type: str
    visibility: str = "public"
    extra: Dict[str, Any] = Field(default_factory=dict)


class StorageBackend(ABC):
    """Base class for storage backends.

    This class defines the interface that all storage backends must implement.
    Storage backends are responsible for:
    - Storing and retrieving artifacts
    - Managing artifact metadata
    - Listing available artifacts
    - Cleaning up resources
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend.

        This method should:
        - Set up any required resources
        - Create necessary directories/tables
        - Establish connections if needed
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend.

        This method should:
        - Clean up any resources
        - Close connections
        - Ensure data is persisted
        """
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

        Raises:
            StorageError: If storage fails
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

        Raises:
            KeyError: If artifact not found
            StorageError: If retrieval fails
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

        Raises:
            KeyError: If artifact not found
            StorageError: If deletion fails
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

        Raises:
            StorageError: If listing fails
        """
        pass
