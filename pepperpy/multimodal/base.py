"""Base classes and interfaces for the multimodal processing system.

This module provides the core abstractions for multimodal processing:
- MultimodalComponent: Base class for all multimodal components
- MultimodalProcessor: Base class for all multimodal processors
- MultimodalProvider: Base class for all multimodal providers
- MultimodalError: Base exception for multimodal-related errors
- DataFormat: Enum for supported data formats
- ContentType: Enum for supported content types
"""

import abc
import enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union

from pydantic import BaseModel, Field

from pepperpy.core.common.base import BaseComponent


class MultimodalError(Exception):
    """Base exception for multimodal-related errors."""

    def __init__(
        self,
        message: str,
        *,
        component: Optional[str] = None,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            component: Optional component name that caused the error
            provider: Optional provider name that caused the error
            details: Optional additional details
        """
        super().__init__(message)
        self.component = component
        self.provider = provider
        self.details = details or {}


class DataFormat(str, enum.Enum):
    """Supported data formats for multimodal content."""

    # Audio formats
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"

    # Image formats
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"

    # Video formats
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    WEBM = "webm"

    # Text formats
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"

    # Vector formats
    VECTOR = "vector"
    EMBEDDING = "embedding"


class ContentType(str, enum.Enum):
    """Supported content types for multimodal processing."""

    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    VECTOR = "vector"
    MULTIMODAL = "multimodal"


class MultimodalMetadata(BaseModel):
    """Common metadata for multimodal content."""

    content_type: ContentType = Field(description="Content type")
    format: DataFormat = Field(description="Data format")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    source: Optional[str] = Field(default=None, description="Content source")
    duration: Optional[float] = Field(
        default=None, description="Content duration in seconds"
    )
    size: Optional[int] = Field(default=None, description="Content size in bytes")
    additional: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MultimodalComponent(BaseComponent):
    """Base class for all multimodal components."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_content_types: Optional[List[ContentType]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize multimodal component.

        Args:
            name: Component name
            config: Optional configuration
            supported_content_types: List of supported content types
            supported_formats: List of supported data formats
        """
        super().__init__(name)
        self._config = config or {}
        self._supported_content_types = supported_content_types or []
        self._supported_formats = supported_formats or []

    @property
    def supported_content_types(self) -> List[ContentType]:
        """Get supported content types.

        Returns:
            List of supported content types
        """
        return self._supported_content_types

    @property
    def supported_formats(self) -> List[DataFormat]:
        """Get supported data formats.

        Returns:
            List of supported data formats
        """
        return self._supported_formats

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Check if content type is supported.

        Args:
            content_type: Content type to check

        Returns:
            True if supported, False otherwise
        """
        return (
            not self._supported_content_types
            or content_type in self._supported_content_types
        )

    def supports_format(self, format: DataFormat) -> bool:
        """Check if data format is supported.

        Args:
            format: Data format to check

        Returns:
            True if supported, False otherwise
        """
        return not self._supported_formats or format in self._supported_formats


# Type variable for generic processors
T = TypeVar("T")
U = TypeVar("U")


class MultimodalProcessor(MultimodalComponent, abc.ABC):
    """Base class for all multimodal processors."""

    @abc.abstractmethod
    async def process(self, data: T, **kwargs: Any) -> U:
        """Process multimodal data.

        Args:
            data: Input data to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed data

        Raises:
            MultimodalError: If processing fails
        """
        pass


class MultimodalProvider(MultimodalComponent, abc.ABC):
    """Base class for all multimodal providers."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            MultimodalError: If initialization fails
        """
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.

        Raises:
            MultimodalError: If shutdown fails
        """
        pass


class FileHandler(Protocol):
    """Protocol for file handling operations."""

    async def save(self, data: Any, path: Union[str, Path], **kwargs: Any) -> Path:
        """Save data to file.

        Args:
            data: Data to save
            path: Output file path
            **kwargs: Additional parameters

        Returns:
            Path to saved file

        Raises:
            MultimodalError: If saving fails
        """
        ...

    async def load(self, path: Union[str, Path], **kwargs: Any) -> Any:
        """Load data from file.

        Args:
            path: Input file path
            **kwargs: Additional parameters

        Returns:
            Loaded data

        Raises:
            MultimodalError: If loading fails
        """
        ...
