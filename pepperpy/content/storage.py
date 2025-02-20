"""Content storage implementations.

This module provides implementations for storing and retrieving content:
- ContentStorage: Base class for content storage
- LocalContentStorage: Storage implementation using local filesystem
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union
from uuid import UUID

from pepperpy.content.base import Content, ContentMetadata, ContentType
from pepperpy.content.loaders import (
    FileContentLoader,
    TextContentLoader,
)


class ContentStorage(ABC):
    """Base class for content storage."""

    @abstractmethod
    def save(self, content: Content) -> UUID:
        """Save content to storage.

        Args:
            content: Content to save

        Returns:
            ID of the saved content
        """
        pass

    @abstractmethod
    def load(self, content_id: UUID) -> Content:
        """Load content from storage.

        Args:
            content_id: ID of the content to load

        Returns:
            Loaded content
        """
        pass

    @abstractmethod
    def delete(self, content_id: UUID) -> None:
        """Delete content from storage.

        Args:
            content_id: ID of the content to delete
        """
        pass

    @abstractmethod
    def list(
        self, content_type: Optional[ContentType] = None
    ) -> Dict[UUID, ContentMetadata]:
        """List available content.

        Args:
            content_type: Optional filter by content type

        Returns:
            Dictionary mapping content IDs to metadata
        """
        pass


class LocalContentStorage(ContentStorage):
    """Content storage using local filesystem."""

    def __init__(self, root_dir: Union[str, Path]):
        """Initialize local storage.

        Args:
            root_dir: Root directory for content storage
        """
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different content types
        self.content_dir = self.root_dir / "content"
        self.metadata_dir = self.root_dir / "metadata"
        self.content_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)

        # Initialize content loaders
        self.loaders = {
            ContentType.TEXT: TextContentLoader(),
            ContentType.FILE: FileContentLoader(),
        }

    def save(self, content: Content) -> UUID:
        """Save content to local storage.

        Args:
            content: Content to save

        Returns:
            ID of the saved content

        Raises:
            ValueError: If content type is not supported
        """
        if content.type not in self.loaders:
            raise ValueError(f"Unsupported content type: {content.type}")

        # Save content data
        content_path = self.content_dir / str(content.metadata.id)
        content.save(content_path)

        # Save metadata
        metadata_path = self.metadata_dir / f"{content.metadata.id}.json"
        metadata_dict = {
            "id": str(content.metadata.id),
            "type": content.metadata.type.name,
            "name": content.metadata.name,
            "created_at": content.metadata.created_at.isoformat(),
            "modified_at": content.metadata.modified_at.isoformat(),
            "size": content.metadata.size,
            "mime_type": content.metadata.mime_type,
            "encoding": content.metadata.encoding,
            "tags": content.metadata.tags,
            "extra": content.metadata.extra,
        }
        metadata_path.write_text(json.dumps(metadata_dict, indent=2))

        return content.metadata.id

    def load(self, content_id: UUID) -> Content:
        """Load content from local storage.

        Args:
            content_id: ID of the content to load

        Returns:
            Loaded content

        Raises:
            FileNotFoundError: If content or metadata not found
            ValueError: If content type is not supported
        """
        # Load metadata
        metadata_path = self.metadata_dir / f"{content_id}.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Content not found: {content_id}")

        metadata_dict = json.loads(metadata_path.read_text())
        metadata = ContentMetadata(
            id=UUID(metadata_dict["id"]),
            type=ContentType[metadata_dict["type"]],
            name=metadata_dict["name"],
            created_at=datetime.fromisoformat(metadata_dict["created_at"]),
            modified_at=datetime.fromisoformat(metadata_dict["modified_at"]),
            size=metadata_dict["size"],
            mime_type=metadata_dict["mime_type"],
            encoding=metadata_dict["encoding"],
            tags=metadata_dict["tags"],
            extra=metadata_dict["extra"],
        )

        # Load content data
        content_path = self.content_dir / str(content_id)
        if not content_path.exists():
            raise FileNotFoundError(f"Content data not found: {content_id}")

        loader = self.loaders.get(metadata.type)
        if loader is None:
            raise ValueError(f"Unsupported content type: {metadata.type}")

        return loader.load(content_path, metadata=metadata)

    def delete(self, content_id: UUID) -> None:
        """Delete content from local storage.

        Args:
            content_id: ID of the content to delete

        Raises:
            FileNotFoundError: If content not found
        """
        content_path = self.content_dir / str(content_id)
        metadata_path = self.metadata_dir / f"{content_id}.json"

        if not content_path.exists() and not metadata_path.exists():
            raise FileNotFoundError(f"Content not found: {content_id}")

        if content_path.exists():
            content_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()

    def list(
        self, content_type: Optional[ContentType] = None
    ) -> Dict[UUID, ContentMetadata]:
        """List available content.

        Args:
            content_type: Optional filter by content type

        Returns:
            Dictionary mapping content IDs to metadata
        """
        results = {}
        for metadata_path in self.metadata_dir.glob("*.json"):
            metadata_dict = json.loads(metadata_path.read_text())
            metadata_type = ContentType[metadata_dict["type"]]

            if content_type is None or metadata_type == content_type:
                metadata = ContentMetadata(
                    id=UUID(metadata_dict["id"]),
                    type=metadata_type,
                    name=metadata_dict["name"],
                    created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                    modified_at=datetime.fromisoformat(metadata_dict["modified_at"]),
                    size=metadata_dict["size"],
                    mime_type=metadata_dict["mime_type"],
                    encoding=metadata_dict["encoding"],
                    tags=metadata_dict["tags"],
                    extra=metadata_dict["extra"],
                )
                results[metadata.id] = metadata

        return results
