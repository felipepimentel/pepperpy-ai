"""Content processing module for PepperPy.

This module provides functionality for processing various types of content:
- Documents (PDF, Word, etc.)
- Images
- Audio
- Video
"""

from pepperpy.content_processing.base import (
    ContentProcessor,
    ContentType,
    ProcessingResult,
    create_processor,
)
from pepperpy.content_processing.errors import (
    ContentProcessingConfigError,
    ContentProcessingError,
    ContentProcessingIOError,
    ProviderNotFoundError,
    UnsupportedContentTypeError,
)
from pepperpy.content_processing.lazy import (
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
