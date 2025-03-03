"""Public Interface for Storage

This module provides a stable public interface for the storage functionality.
It exposes the core storage abstractions and implementations that are
considered part of the public API.

Core Components:
    StorageCapability: Storage capability for agents
    FileStorage: Interface for file storage operations
    ObjectStorage: Interface for object storage operations
"""

from abc import ABC, abstractmethod
from typing import Any, List, Union


class StorageCapability:
    """Storage capability for agents.

    This class provides storage capabilities for agents, including
    file and object storage operations.
    """

    def __init__(self, name: str = "storage"):
        """Initialize the storage capability.

        Args:
            name: Capability name

        """
        self.name = name
        self.file_storage = None
        self.object_storage = None

    def set_file_storage(self, file_storage: "FileStorage") -> None:
        """Set the file storage provider.

        Args:
            file_storage: File storage provider

        """
        self.file_storage = file_storage

    def set_object_storage(self, object_storage: "ObjectStorage") -> None:
        """Set the object storage provider.

        Args:
            object_storage: Object storage provider

        """
        self.object_storage = object_storage

    async def save_file(self, path: str, content: Union[str, bytes]) -> str:
        """Save a file.

        Args:
            path: File path
            content: File content

        Returns:
            File path

        Raises:
            ValueError: If file storage is not set

        """
        if not self.file_storage:
            raise ValueError("File storage not set")
        return await self.file_storage.save(path, content)

    async def load_file(self, path: str) -> Union[str, bytes]:
        """Load a file.

        Args:
            path: File path

        Returns:
            File content

        Raises:
            ValueError: If file storage is not set

        """
        if not self.file_storage:
            raise ValueError("File storage not set")
        return await self.file_storage.load(path)

    async def save_object(self, key: str, obj: Any) -> str:
        """Save an object.

        Args:
            key: Object key
            obj: Object to save

        Returns:
            Object key

        Raises:
            ValueError: If object storage is not set

        """
        if not self.object_storage:
            raise ValueError("Object storage not set")
        return await self.object_storage.save(key, obj)

    async def load_object(self, key: str) -> Any:
        """Load an object.

        Args:
            key: Object key

        Returns:
            Loaded object

        Raises:
            ValueError: If object storage is not set

        """
        if not self.object_storage:
            raise ValueError("Object storage not set")
        return await self.object_storage.load(key)


class FileStorage(ABC):
    """Interface for file storage operations.

    This class defines the interface for file storage operations,
    including saving, loading, and deleting files.
    """

    def __init__(self, name: str):
        """Initialize the file storage.

        Args:
            name: Storage name

        """
        self.name = name

    @abstractmethod
    async def save(self, path: str, content: Union[str, bytes]) -> str:
        """Save a file.

        Args:
            path: File path
            content: File content

        Returns:
            File path

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement save method")

    @abstractmethod
    async def load(self, path: str) -> Union[str, bytes]:
        """Load a file.

        Args:
            path: File path

        Returns:
            File content

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement load method")

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete a file.

        Args:
            path: File path

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement delete method")

    @abstractmethod
    async def list(self, path: str) -> List[str]:
        """List files in a directory.

        Args:
            path: Directory path

        Returns:
            List of file paths

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement list method")


class ObjectStorage(ABC):
    """Interface for object storage operations.

    This class defines the interface for object storage operations,
    including saving, loading, and deleting objects.
    """

    def __init__(self, name: str):
        """Initialize the object storage.

        Args:
            name: Storage name

        """
        self.name = name

    @abstractmethod
    async def save(self, key: str, obj: Any) -> str:
        """Save an object.

        Args:
            key: Object key
            obj: Object to save

        Returns:
            Object key

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement save method")

    @abstractmethod
    async def load(self, key: str) -> Any:
        """Load an object.

        Args:
            key: Object key

        Returns:
            Loaded object

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement load method")

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete an object.

        Args:
            key: Object key

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement delete method")

    @abstractmethod
    async def list(self, prefix: str = "") -> List[str]:
        """List objects with a prefix.

        Args:
            prefix: Key prefix

        Returns:
            List of object keys

        Raises:
            NotImplementedError: If the subclass does not implement this method

        """
        raise NotImplementedError("Subclasses must implement list method")


# Export public classes
__all__ = [
    "FileStorage",
    "ObjectStorage",
    "StorageCapability",
]
