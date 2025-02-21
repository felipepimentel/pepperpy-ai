"""Base content module.

This module provides the base interfaces for content management and synthesis.
It defines the core abstractions for handling different types of content and
synthesizing new content from existing sources.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from pepperpy.core.errors import PepperpyError
from pepperpy.core.extensions import Extension


class ContentError(PepperpyError):
    """Base class for content-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize content error.

        Args:
            message: Error message
            details: Optional error details
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message=message,
            details=details,
            recovery_hint=recovery_hint,
            error_code="ERR-107",
        )


class ContentType(Enum):
    """Supported content types."""

    TEXT = auto()
    FILE = auto()
    IMAGE = auto()
    AUDIO = auto()
    VIDEO = auto()
    BINARY = auto()


class ContentMetadata(BaseModel):
    """Metadata for content items.

    Attributes:
        id: Content ID
        type: Content type
        source: Content source
        created_at: Creation timestamp
        updated_at: Last update timestamp
        tags: Content tags
        metadata: Additional metadata
    """

    id: str
    type: str
    source: str
    created_at: str
    updated_at: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Content(ABC):
    """Base class for content items."""

    def __init__(
        self,
        content_type: ContentType,
        name: str,
        data: Any,
        metadata: Optional[ContentMetadata] = None,
    ) -> None:
        """Initialize content item.

        Args:
            content_type: Type of content
            name: Name of the content
            data: Content data
            metadata: Optional content metadata
        """
        self.type = content_type
        self.name = name
        self.data = data
        self.metadata = metadata or ContentMetadata(
            id=str(uuid4()),
            type=content_type.name,
            source="local",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        self.size = self._calculate_size()

    @abstractmethod
    def _calculate_size(self) -> int:
        """Calculate the size of the content in bytes.

        Returns:
            Size in bytes
        """
        pass

    @abstractmethod
    def load(self) -> Any:
        """Load the content data.

        Returns:
            Content data
        """
        pass

    @abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """Save the content to a file.

        Args:
            path: Path to save the content to
        """
        pass


class ContentConfig(BaseModel):
    """Configuration for content providers.

    Attributes:
        name: Provider name
        description: Provider description
        parameters: Additional parameters
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


T = TypeVar("T", bound=ContentConfig)


class BaseContent(Extension[T], ABC):
    """Base class for content providers.

    This class defines the interface that all content providers must implement.
    It provides methods for storing, retrieving, and managing content items.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[T] = None,
    ) -> None:
        """Initialize content provider.

        Args:
            name: Provider name
            version: Provider version
            config: Optional provider configuration
        """
        super().__init__(name, version, config)

    @abstractmethod
    async def store(
        self,
        content: Any,
        metadata: Optional[ContentMetadata] = None,
    ) -> str:
        """Store content item.

        Args:
            content: Content to store
            metadata: Optional content metadata

        Returns:
            Content ID

        Raises:
            ContentError: If content cannot be stored
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        content_id: str,
    ) -> Any:
        """Retrieve content item.

        Args:
            content_id: Content ID

        Returns:
            Content item

        Raises:
            ContentError: If content cannot be retrieved
        """
        pass

    @abstractmethod
    async def delete(
        self,
        content_id: str,
    ) -> None:
        """Delete content item.

        Args:
            content_id: Content ID

        Raises:
            ContentError: If content cannot be deleted
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def update(
        self,
        content_id: str,
        content: Any,
        metadata: Optional[ContentMetadata] = None,
    ) -> None:
        """Update content item.

        Args:
            content_id: Content ID
            content: New content
            metadata: Optional new metadata

        Raises:
            ContentError: If content cannot be updated
        """
        pass

    @abstractmethod
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
        pass


class SynthesisConfig(BaseModel):
    """Configuration for content synthesis.

    Attributes:
        name: Synthesizer name
        description: Synthesizer description
        parameters: Additional parameters
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


S = TypeVar("S", bound=SynthesisConfig)


class BaseSynthesis(Extension[S], ABC):
    """Base class for content synthesis.

    This class defines the interface that all content synthesizers must implement.
    It provides methods for synthesizing new content from existing sources.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[S] = None,
    ) -> None:
        """Initialize content synthesizer.

        Args:
            name: Synthesizer name
            version: Synthesizer version
            config: Optional synthesizer configuration
        """
        super().__init__(name, version, config)

    @abstractmethod
    async def synthesize(
        self,
        sources: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Synthesize new content from sources.

        Args:
            sources: Source content items
            parameters: Optional synthesis parameters

        Returns:
            Synthesized content

        Raises:
            ContentError: If content cannot be synthesized
        """
        pass

    @abstractmethod
    async def validate(
        self,
        content: Any,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate synthesized content.

        Args:
            content: Content to validate
            parameters: Optional validation parameters

        Returns:
            True if valid, False otherwise

        Raises:
            ContentError: If content cannot be validated
        """
        pass

    @abstractmethod
    async def refine(
        self,
        content: Any,
        feedback: Any,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Refine synthesized content based on feedback.

        Args:
            content: Content to refine
            feedback: Feedback for refinement
            parameters: Optional refinement parameters

        Returns:
            Refined content

        Raises:
            ContentError: If content cannot be refined
        """
        pass
