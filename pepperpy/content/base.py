"""Base types and interfaces for content management.

This module defines the core abstractions for managing content in Pepperpy:
- Content: Base class for all content types
- ContentType: Enum of supported content types
- ContentMetadata: Class for storing content metadata
- ContentManager: Interface for content management operations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4


class ContentType(Enum):
    """Supported content types."""

    TEXT = auto()
    FILE = auto()
    IMAGE = auto()
    AUDIO = auto()
    VIDEO = auto()
    BINARY = auto()


@dataclass
class ContentMetadata:
    """Metadata for content items."""

    id: UUID
    type: ContentType
    name: str
    created_at: datetime
    modified_at: datetime
    size: int
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = {}
        if self.extra is None:
            self.extra = {}


class Content(ABC):
    """Base class for all content types."""

    def __init__(
        self,
        content_type: ContentType,
        name: str,
        data: Any = None,
        metadata: Optional[ContentMetadata] = None,
    ):
        """Initialize content.

        Args:
            content_type: Type of the content
            name: Name of the content
            data: Content data
            metadata: Content metadata
        """
        self.type = content_type
        self.name = name
        self.data = data

        if metadata is None:
            now = datetime.utcnow()
            self.metadata = ContentMetadata(
                id=uuid4(),
                type=content_type,
                name=name,
                created_at=now,
                modified_at=now,
                size=self._calculate_size(),
            )
        else:
            self.metadata = metadata

    @abstractmethod
    def _calculate_size(self) -> int:
        """Calculate the size of the content in bytes."""
        pass

    @abstractmethod
    def load(self) -> Any:
        """Load the content data."""
        pass

    @abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """Save the content to a file.

        Args:
            path: Path to save the content to
        """
        pass


class ContentManager(ABC):
    """Interface for content management operations."""

    @abstractmethod
    def load(self, content_id: UUID) -> Content:
        """Load content by ID.

        Args:
            content_id: ID of the content to load

        Returns:
            The loaded content
        """
        pass

    @abstractmethod
    def save(self, content: Content) -> UUID:
        """Save content.

        Args:
            content: Content to save

        Returns:
            ID of the saved content
        """
        pass

    @abstractmethod
    def delete(self, content_id: UUID) -> None:
        """Delete content by ID.

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
