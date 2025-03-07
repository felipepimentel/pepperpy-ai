"""Base interfaces for multimodal processing.

This module provides the core abstractions for multimodal processing:
- ContentType: Enumeration of content types
- DataFormat: Enumeration of data formats
- MultimodalError: Base exception for multimodal errors
- MultimodalProcessor: Base class for multimodal processors
- MultimodalProvider: Base class for multimodal service providers
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(str, Enum):
    """Types of content supported by the multimodal system.

    Attributes:
        TEXT: Text content
        IMAGE: Image content
        AUDIO: Audio content
        VIDEO: Video content
        DOCUMENT: Document content
        TABULAR: Tabular content
        VECTOR: Vector content
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    TABULAR = "tabular"
    VECTOR = "vector"


class DataFormat(str, Enum):
    """Data formats supported by the multimodal system.

    Attributes:
        JSON: JSON format
        XML: XML format
        CSV: CSV format
        YAML: YAML format
        MARKDOWN: Markdown format
        HTML: HTML format
        PDF: PDF format
        DOCX: Microsoft Word format
        XLSX: Microsoft Excel format
        PPTX: Microsoft PowerPoint format
        PNG: PNG image format
        JPEG: JPEG image format
        GIF: GIF image format
        SVG: SVG image format
        MP3: MP3 audio format
        WAV: WAV audio format
        OGG: OGG audio format
        FLAC: FLAC audio format
        MP4: MP4 video format
        AVI: AVI video format
        MKV: MKV video format
    """

    # Text formats
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    YAML = "yaml"
    MARKDOWN = "markdown"
    HTML = "html"

    # Document formats
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"

    # Image formats
    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    SVG = "svg"

    # Audio formats
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"

    # Video formats
    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"


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
        self.component = component
        self.provider = provider
        self.details = details or {}
        super().__init__(message)


class MultimodalProcessor(ABC):
    """Base class for all multimodal processors."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_content_types: Optional[List[ContentType]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize multimodal processor.

        Args:
            name: Processor name
            config: Optional configuration
            supported_content_types: List of supported content types
            supported_formats: List of supported data formats
        """
        self.name = name
        self._config = config or {}
        self.supported_content_types = supported_content_types or []
        self.supported_formats = supported_formats or []

    @abstractmethod
    async def process(self, content: Any) -> Any:
        """Process content.

        Args:
            content: Input content to process

        Returns:
            Processed content

        Raises:
            MultimodalError: If processing fails
        """
        pass


class MultimodalProvider(ABC):
    """Base class for multimodal service providers."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_content_types: Optional[List[ContentType]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize multimodal provider.

        Args:
            name: Provider name
            config: Optional configuration
            supported_content_types: List of supported content types
            supported_formats: List of supported data formats
        """
        self.name = name
        self._config = config or {}
        self.supported_content_types = supported_content_types or []
        self.supported_formats = supported_formats or []

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            MultimodalError: If initialization fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.

        Raises:
            MultimodalError: If shutdown fails
        """
        pass
