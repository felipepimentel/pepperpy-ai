"""
PepperPy Content Module.

Module for content processing in the PepperPy framework.
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
from pepperpy.content.result import (
    DocumentResult,
    JSONResult,
    TextResult,
)
from pepperpy.content.tasks import (
    ContentWorkflow,
    DocumentProcessor,
    Processor,
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
    # Results
    "DocumentResult",
    "JSONResult",
    "TextResult",
    # Tasks
    "ContentWorkflow",
    "DocumentProcessor",
    "Processor",
]
