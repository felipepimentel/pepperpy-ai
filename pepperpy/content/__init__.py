"""Content processing module for PepperPy.

This module provides functionality for processing various types of content:
- Documents (PDF, Word, etc.)
- Images
- Audio
- Video
"""

from pepperpy.content.base import (
    ContentProcessor,
    ContentType,
    ProcessingResult,
    create_processor,
)
from pepperpy.core.errors import PepperpyError


class ContentProcessingError(PepperpyError):
    """Base error for content processing."""

    pass


class ContentProcessingConfigError(ContentProcessingError):
    """Error related to configuration of content processors."""

    pass


class ContentProcessingIOError(ContentProcessingError):
    """IO error during content processing."""

    pass


class UnsupportedContentTypeError(ContentProcessingError):
    """Error when content type is not supported."""

    pass


class ProviderNotFoundError(ContentProcessingError):
    """Error when content processor provider is not found."""

    pass


from pepperpy.content.lazy import (
    AVAILABLE_PROCESSORS,
    DEFAULT_PROCESSORS,
)

from .archives import ArchiveError, ArchiveHandler
from .integration import ContentRAGError, ContentRAGProcessor

__all__ = [
    # Base
    "ContentProcessor",
    "ContentProcessingError",
    "ContentProcessingConfigError",
    "ContentProcessingIOError",
    "UnsupportedContentTypeError",
    "ProviderNotFoundError",
    "ContentType",
    "ProcessingResult",
    "create_processor",
    # Lazy loading
    "DEFAULT_PROCESSORS",
    "AVAILABLE_PROCESSORS",
    # Archives
    "ArchiveError",
    "ArchiveHandler",
    # RAG integration
    "ContentRAGError",
    "ContentRAGProcessor",
]
