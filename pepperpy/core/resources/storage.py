"""Resource storage system.

This module provides storage implementations for resources.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.errors import ResourceError
from pepperpy.resources.base import BaseResource, ResourceType

# Configure logging
logger = logging.getLogger(__name__)


class FileResource(BaseResource):
    """File resource implementation.

    This class provides a file-based resource implementation.
    """

    def __init__(
        self,
        id: str,
        path: Union[str, Path],
        content_type: Optional[str] = None,
        encoding: str = "utf-8",
        **kwargs,
    ) -> None:
        """Initialize resource.

        Args:
            id: Resource ID
            path: Resource path
            content_type: Content type
            encoding: File encoding
            **kwargs: Additional metadata
        """
        super().__init__(id, ResourceType.FILE, **kwargs)
        self._path = Path(path)
        self._content: Optional[Any] = None
        self.metadata.content_type = content_type
        self._encoding = encoding

    @property
    def path(self) -> Path:
        """Get resource path."""
        return self._path

    @property
    def content(self) -> Optional[Any]:
        """Get resource content."""
        return self._content

    async def _load(self) -> None:
        """Load resource from file."""
        if not self._path.exists():
            raise ResourceError(f"File not found: {self._path}")

        try:
            self.metadata.size = self._path.stat().st_size
            content_type = self.metadata.content_type or self._path.suffix.lstrip(".")

            if content_type in ["json"]:
                async with asyncio.Lock():
                    with open(self._path, "r", encoding=self._encoding) as f:
                        self._content = json.load(f)
            elif content_type in ["pickle", "pkl"]:
                async with asyncio.Lock():
                    with open(self._path, "rb") as f:
                        self._content = pickle.load(f)
            else:
                async with asyncio.Lock():
                    with open(self._path, "r", encoding=self._encoding) as f:
                        self._content = f.read()
        except Exception as e:
            raise ResourceError(f"Failed to load file {self._path}: {e}") from e

    async def _save(self) -> None:
        """Save resource to file."""
        if self._content is None:
            raise ResourceError("No content to save")

        try:
            # Create parent directories if needed
            self._path.parent.mkdir(parents=True, exist_ok=True)

            content_type = self.metadata.content_type or self._path.suffix.lstrip(".")

            if content_type in ["json"]:
                async with asyncio.Lock():
                    with open(self._path, "w", encoding=self._encoding) as f:
                        json.dump(self._content, f, indent=2)
            elif content_type in ["pickle", "pkl"]:
                async with asyncio.Lock():
                    with open(self._path, "wb") as f:
                        pickle.dump(self._content, f)
            else:
                async with asyncio.Lock():
                    with open(self._path, "w", encoding=self._encoding) as f:
                        f.write(str(self._content))

            self.metadata.size = self._path.stat().st_size
        except Exception as e:
            raise ResourceError(f"Failed to save file {self._path}: {e}") from e

    async def _delete(self) -> None:
        """Delete resource file."""
        try:
            if self._path.exists():
                self._path.unlink()
            self._content = None
            self.metadata.size = 0
        except Exception as e:
            raise ResourceError(f"Failed to delete file {self._path}: {e}") from e

    async def _initialize(self) -> None:
        """Initialize resource."""
        pass

    async def _execute(self) -> None:
        """Execute resource."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resource."""
        await self.delete()


class MemoryResource(BaseResource):
    """Memory resource implementation.

    This class provides a memory-based resource implementation.
    """

    def __init__(
        self,
        id: str,
        content: Any = None,
        content_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize resource.

        Args:
            id: Resource ID
            content: Initial content
            content_type: Content type
            **kwargs: Additional metadata
        """
        super().__init__(id, ResourceType.MEMORY, **kwargs)
        self._content = content
        self.metadata.content_type = content_type

    @property
    def content(self) -> Any:
        """Get resource content."""
        return self._content

    @content.setter
    def content(self, value: Any) -> None:
        """Set resource content."""
        self._content = value
        self.metadata.updated_at = datetime.utcnow()

    async def _load(self) -> None:
        """Load resource from memory."""
        # Memory resources are already loaded
        pass

    async def _save(self) -> None:
        """Save resource to memory."""
        # Memory resources are already saved
        pass

    async def _delete(self) -> None:
        """Delete resource from memory."""
        self._content = None

    async def _initialize(self) -> None:
        """Initialize resource."""
        pass

    async def _execute(self) -> None:
        """Execute resource."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resource."""
        await self.delete()


class ResourceStorage:
    """Resource storage implementation.

    This class provides methods for storing and retrieving resources.
    """

    def __init__(self, base_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize storage.

        Args:
            base_path: Base path for file resources
        """
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._memory_resources: Dict[str, MemoryResource] = {}
        self._file_resources: Dict[str, FileResource] = {}
        self._lock = asyncio.Lock()

    async def store(
        self,
        id: str,
        content: Any,
        resource_type: ResourceType = ResourceType.MEMORY,
        **kwargs,
    ) -> BaseResource:
        """Store resource.

        Args:
            id: Resource ID
            content: Resource content
            resource_type: Resource type
            **kwargs: Additional metadata

        Returns:
            BaseResource: Stored resource

        Raises:
            ResourceError: If resource cannot be stored
        """
        async with self._lock:
            try:
                if resource_type == ResourceType.MEMORY:
                    resource = MemoryResource(id, content, **kwargs)
                    self._memory_resources[id] = resource
                elif resource_type == ResourceType.FILE:
                    path = kwargs.pop("path", self._base_path / id)
                    resource = FileResource(id, path, **kwargs)
                    resource._content = content
                    await resource.save()
                    self._file_resources[id] = resource
                else:
                    raise ResourceError(f"Unsupported resource type: {resource_type}")

                return resource
            except Exception as e:
                raise ResourceError(f"Failed to store resource {id}: {e}") from e

    async def retrieve(self, id: str) -> Optional[BaseResource]:
        """Retrieve resource.

        Args:
            id: Resource ID

        Returns:
            Optional[BaseResource]: Retrieved resource
        """
        resource = self._memory_resources.get(id) or self._file_resources.get(id)
        if resource and resource.state != resource.state.LOADED:
            await resource.load()
        return resource

    async def delete(self, id: str) -> None:
        """Delete resource.

        Args:
            id: Resource ID

        Raises:
            ResourceError: If resource not found
        """
        async with self._lock:
            resource = self._memory_resources.get(id) or self._file_resources.get(id)
            if not resource:
                raise ResourceError(f"Resource not found: {id}")

            await resource.delete()

            if isinstance(resource, MemoryResource):
                del self._memory_resources[id]
            else:
                del self._file_resources[id]
