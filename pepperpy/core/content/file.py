"""File-based content provider implementation.

This module provides a content provider that stores content in the local filesystem.
It implements the BaseContent interface and provides methods for storing, retrieving,
and managing content items using files and directories.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.content.base import (
    BaseContent,
    ContentConfig,
    ContentError,
    ContentMetadata,
)
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


class FileContentConfig(ContentConfig):
    """Configuration for file-based content provider.

    Attributes:
        name: Provider name
        description: Provider description
        base_path: Base directory for content storage
        create_dirs: Whether to create missing directories
        parameters: Additional parameters
        metadata: Additional metadata
    """

    base_path: str
    create_dirs: bool = True


class FileContent(BaseContent[FileContentConfig]):
    """File-based content provider implementation."""

    def __init__(
        self,
        name: str = "file_content",
        version: str = "0.1.0",
        config: Optional[FileContentConfig] = None,
    ) -> None:
        """Initialize file content provider.

        Args:
            name: Provider name
            version: Provider version
            config: Optional provider configuration
        """
        if config is None:
            config = FileContentConfig(
                name=name,
                base_path=os.path.join(os.getcwd(), "content"),
            )
        super().__init__(name, version, config)
        self._base_path = Path(config.base_path)
        if config.create_dirs:
            self._base_path.mkdir(parents=True, exist_ok=True)

    async def _initialize(self) -> None:
        """Initialize provider resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up provider resources."""
        pass

    async def store(
        self,
        content: Any,
        metadata: Optional[ContentMetadata] = None,
    ) -> str:
        """Store content in file.

        Args:
            content: Content to store
            metadata: Optional content metadata

        Returns:
            Content ID

        Raises:
            ContentError: If content cannot be stored
        """
        try:
            # Generate content ID and metadata
            now = datetime.utcnow().isoformat()
            content_id = f"{now}-{self._generate_id()}"

            if metadata is None:
                metadata = ContentMetadata(
                    id=content_id,
                    type="file",
                    source="local",
                    created_at=now,
                    updated_at=now,
                )

            # Create content directory
            content_dir = self._base_path / content_id
            content_dir.mkdir(parents=True, exist_ok=True)

            # Write content and metadata
            content_path = content_dir / "content"
            metadata_path = content_dir / "metadata.json"

            if isinstance(content, (str, bytes)):
                mode = "wb" if isinstance(content, bytes) else "w"
                with open(content_path, mode) as f:
                    f.write(content)
            else:
                with open(content_path, "w") as f:
                    json.dump(content, f)

            with open(metadata_path, "w") as f:
                json.dump(metadata.dict(), f)

            return content_id

        except Exception as e:
            raise ContentError(
                message=f"Failed to store content: {e}",
                details={"content_id": content_id},
            )

    async def retrieve(
        self,
        content_id: str,
    ) -> Any:
        """Retrieve content from file.

        Args:
            content_id: Content ID

        Returns:
            Content item

        Raises:
            ContentError: If content cannot be retrieved
        """
        try:
            content_dir = self._base_path / content_id
            content_path = content_dir / "content"
            metadata_path = content_dir / "metadata.json"

            if not content_dir.exists():
                raise ContentError(
                    message=f"Content not found: {content_id}",
                    details={"content_id": content_id},
                )

            # Read metadata to determine content type
            with open(metadata_path, "r") as f:
                metadata = ContentMetadata(**json.load(f))

            # Read content based on type
            if metadata.type in ["text", "string"]:
                with open(content_path, "r") as f:
                    return f.read()
            elif metadata.type == "binary":
                with open(content_path, "rb") as f:
                    return f.read()
            else:
                with open(content_path, "r") as f:
                    return json.load(f)

        except ContentError:
            raise
        except Exception as e:
            raise ContentError(
                message=f"Failed to retrieve content: {e}",
                details={"content_id": content_id},
            )

    async def delete(
        self,
        content_id: str,
    ) -> None:
        """Delete content from file.

        Args:
            content_id: Content ID

        Raises:
            ContentError: If content cannot be deleted
        """
        try:
            content_dir = self._base_path / content_id
            if not content_dir.exists():
                raise ContentError(
                    message=f"Content not found: {content_id}",
                    details={"content_id": content_id},
                )

            shutil.rmtree(content_dir)

        except ContentError:
            raise
        except Exception as e:
            raise ContentError(
                message=f"Failed to delete content: {e}",
                details={"content_id": content_id},
            )

    async def list(
        self,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[ContentMetadata]:
        """List content items.

        Args:
            filter_criteria: Optional filter criteria

        Returns:
            List of content metadata

        Raises:
            ContentError: If content cannot be listed
        """
        try:
            result = []
            for content_dir in self._base_path.iterdir():
                if not content_dir.is_dir():
                    continue

                metadata_path = content_dir / "metadata.json"
                if not metadata_path.exists():
                    continue

                with open(metadata_path, "r") as f:
                    metadata = ContentMetadata(**json.load(f))

                if filter_criteria:
                    matches = True
                    for key, value in filter_criteria.items():
                        if getattr(metadata, key, None) != value:
                            matches = False
                            break
                    if not matches:
                        continue

                result.append(metadata)

            return result

        except Exception as e:
            raise ContentError(
                message=f"Failed to list content: {e}",
                details={"filter_criteria": filter_criteria},
            )

    async def update(
        self,
        content_id: str,
        content: Any,
        metadata: Optional[ContentMetadata] = None,
    ) -> None:
        """Update content in file.

        Args:
            content_id: Content ID
            content: New content
            metadata: Optional new metadata

        Raises:
            ContentError: If content cannot be updated
        """
        try:
            content_dir = self._base_path / content_id
            if not content_dir.exists():
                raise ContentError(
                    message=f"Content not found: {content_id}",
                    details={"content_id": content_id},
                )

            # Update content
            content_path = content_dir / "content"
            if isinstance(content, (str, bytes)):
                mode = "wb" if isinstance(content, bytes) else "w"
                with open(content_path, mode) as f:
                    f.write(content)
            else:
                with open(content_path, "w") as f:
                    json.dump(content, f)

            # Update metadata if provided
            if metadata:
                metadata_path = content_dir / "metadata.json"
                with open(metadata_path, "w") as f:
                    json.dump(metadata.dict(), f)

        except ContentError:
            raise
        except Exception as e:
            raise ContentError(
                message=f"Failed to update content: {e}",
                details={"content_id": content_id},
            )

    async def search(
        self,
        query: str,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[ContentMetadata]:
        """Search content items.

        Args:
            query: Search query
            filter_criteria: Optional filter criteria

        Returns:
            List of matching content metadata

        Raises:
            ContentError: If content cannot be searched
        """
        try:
            result = []
            for content_dir in self._base_path.iterdir():
                if not content_dir.is_dir():
                    continue

                metadata_path = content_dir / "metadata.json"
                content_path = content_dir / "content"
                if not metadata_path.exists() or not content_path.exists():
                    continue

                # Load metadata
                with open(metadata_path, "r") as f:
                    metadata = ContentMetadata(**json.load(f))

                # Apply filters
                if filter_criteria:
                    matches = True
                    for key, value in filter_criteria.items():
                        if getattr(metadata, key, None) != value:
                            matches = False
                            break
                    if not matches:
                        continue

                # Search content
                try:
                    with open(content_path, "r") as f:
                        content = f.read()
                        if query.lower() in content.lower():
                            result.append(metadata)
                except:
                    # Skip binary content
                    continue

            return result

        except Exception as e:
            raise ContentError(
                message=f"Failed to search content: {e}",
                details={"query": query, "filter_criteria": filter_criteria},
            )

    def _generate_id(self) -> str:
        """Generate a unique content ID."""
        import uuid

        return str(uuid.uuid4())
