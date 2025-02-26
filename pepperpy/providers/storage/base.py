"""Base interfaces and exceptions for storage providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageProvider(ABC):
    """Base class for storage providers."""

    @abstractmethod
    def store(self, path: Union[str, Path], data: Union[str, bytes]) -> None:
        """Store data in storage.

        Args:
            path: Path to store data at
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from storage.

        Args:
            path: Path to retrieve data from

        Returns:
            bytes: Retrieved data

        Raises:
            StorageError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def delete(self, path: Union[str, Path]) -> bool:
        """Delete data from storage.

        Args:
            path: Path to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
        """
        pass

    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists in storage.

        Args:
            path: Path to check

        Returns:
            bool: True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        pass

    @abstractmethod
    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List files in storage.

        Args:
            path: Optional path to list files from

        Returns:
            List[str]: List of file paths

        Raises:
            StorageError: If list operation fails
        """
        pass

    @abstractmethod
    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get URL for accessing file in storage.

        Args:
            path: Path to file
            expires_in: Optional expiration time in seconds

        Returns:
            str: URL for accessing file

        Raises:
            StorageError: If URL generation fails
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


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageProvider(BaseProvider[StorageMetadata]):
    """Base class for storage providers."""

    @abstractmethod
    def store(self, path: Union[str, Path], data: Union[str, bytes]) -> None:
        """Store data in storage.

        Args:
            path: Path to store data at
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from storage.

        Args:
            path: Path to retrieve data from

        Returns:
            bytes: Retrieved data

        Raises:
            StorageError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def delete(self, path: Union[str, Path]) -> bool:
        """Delete data from storage.

        Args:
            path: Path to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
        """
        pass

    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists in storage.

        Args:
            path: Path to check

        Returns:
            bool: True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        pass

    @abstractmethod
    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List files in storage.

        Args:
            path: Optional path to list files from

        Returns:
            List[str]: List of file paths

        Raises:
            StorageError: If list operation fails
        """
        pass

    @abstractmethod
    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get URL for accessing file in storage.

        Args:
            path: Path to file
            expires_in: Optional expiration time in seconds

        Returns:
            str: URL for accessing file

        Raises:
            StorageError: If URL generation fails
        """
        pass
