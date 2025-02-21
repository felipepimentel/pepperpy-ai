"""Base storage provider interface.

This module defines the base interface for storage providers.
It includes:
- Base storage provider interface
- Storage configuration
- Common storage types
"""

import os
from abc import abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pydantic import BaseModel

from pepperpy.providers.base import BaseProvider, ProviderConfig


class StorageConfig(ProviderConfig):
    """Storage provider configuration.

    Attributes:
        root_path: Root path for storage operations
        create_if_missing: Create directories if missing
        permissions: File/directory permissions
    """

    root_path: Optional[str] = None
    create_if_missing: bool = True
    permissions: Optional[int] = None


class StorageMetadata(BaseModel):
    """Storage item metadata.

    Attributes:
        path: Item path
        size: Item size in bytes
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        content_type: Content type
        metadata: Additional metadata
    """

    path: str
    size: int
    created_at: float
    modified_at: float
    content_type: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseStorageProvider(BaseProvider[StorageMetadata]):
    """Base class for storage providers.

    This class defines the interface that all storage providers must implement.
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize storage provider.

        Args:
            config: Storage configuration
        """
        super().__init__(config)
        self.root_path = config.root_path
        self.create_if_missing = config.create_if_missing
        self.permissions = config.permissions

    @abstractmethod
    async def read(self, path: Union[str, Path]) -> bytes:
        """Read file contents.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            ProviderError: If read fails
        """
        pass

    @abstractmethod
    async def write(
        self,
        path: Union[str, Path],
        data: Union[str, bytes],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageMetadata:
        """Write data to file.

        Args:
            path: File path
            data: Data to write
            metadata: Optional metadata

        Returns:
            File metadata

        Raises:
            ProviderError: If write fails
        """
        pass

    @abstractmethod
    async def delete(self, path: Union[str, Path]) -> None:
        """Delete file or directory.

        Args:
            path: Path to delete

        Raises:
            ProviderError: If deletion fails
        """
        pass

    @abstractmethod
    async def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists.

        Args:
            path: Path to check

        Returns:
            True if path exists

        Raises:
            ProviderError: If check fails
        """
        pass

    @abstractmethod
    async def list(
        self,
        path: Union[str, Path],
        recursive: bool = False,
        include_metadata: bool = False,
    ) -> Union[List[str], List[StorageMetadata]]:
        """List directory contents.

        Args:
            path: Directory path
            recursive: List recursively
            include_metadata: Include metadata

        Returns:
            List of paths or metadata

        Raises:
            ProviderError: If listing fails
        """
        pass

    @abstractmethod
    async def get_metadata(self, path: Union[str, Path]) -> StorageMetadata:
        """Get item metadata.

        Args:
            path: Item path

        Returns:
            Item metadata

        Raises:
            ProviderError: If metadata retrieval fails
        """
        pass

    @abstractmethod
    async def update_metadata(
        self, path: Union[str, Path], metadata: Dict[str, Any]
    ) -> StorageMetadata:
        """Update item metadata.

        Args:
            path: Item path
            metadata: New metadata

        Returns:
            Updated metadata

        Raises:
            ProviderError: If update fails
        """
        pass

    @abstractmethod
    async def stream(self, path: Union[str, Path]) -> AsyncIterator[bytes]:
        """Stream file contents.

        Args:
            path: File path

        Returns:
            Content stream

        Raises:
            ProviderError: If streaming fails
        """
        pass

    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        if self.root_path and not os.path.isabs(self.root_path):
            raise ValueError("Root path must be absolute")
        if self.permissions is not None and not 0 <= self.permissions <= 0o777:
            raise ValueError("Invalid permissions")
