"""Content processing module for PepperPy.

This module provides a unified interface for processing various types of content,
including documents, images, audio, and video files. It supports multiple providers
for each content type and offers a consistent API for content processing operations.

Example:
    >>> from pepperpy import PepperPy
    >>> 
    >>> # Initialize PepperPy with content processing configuration
    >>> pp = PepperPy()
    >>> pp.configure_content_processor(
    ...     content_type='document',
    ...     providers=[
    ...         {
    ...             "type": "pymupdf",
    ...             "config": {
    ...                 "extract_images": True,
    ...                 "extract_tables": True,
    ...             },
    ...         },
    ...         {
    ...             "type": "pandoc",
    ...             "config": {
    ...                 "output_format": "markdown",
    ...             },
    ...         },
    ...     ],
    ... )
    >>> 
    >>> # Process a PDF document
    >>> result = pp.process_content('document.pdf')
    >>> print(result.metadata)
    {
        'title': 'Sample Document',
        'author': 'John Doe',
        'pages': 10,
        'text': 'Extracted text content...',
    }
"""

from .archives import ArchiveError, ArchiveHandler
from .base import (
    ContentProcessor,
    ContentType,
    ProcessingResult,
    create_processor,
)
from .errors import (
    ContentProcessingError,
    ContentProcessingConfigError,
    ContentProcessingIOError,
    UnsupportedContentTypeError,
)
from .integration import ContentRAGError, ContentRAGProcessor
from .processors import (
    AudioProcessor,
    DocumentProcessor,
    ImageProcessor,
    VideoProcessor,
)
from .protected import ProtectedContentError, ProtectedContentHandler

__all__ = [
    # Base
    'ContentProcessor',
    'ContentType',
    'ProcessingResult',
    'create_processor',

    # Errors
    'ContentProcessingError',
    'ContentProcessingConfigError',
    'ContentProcessingIOError',
    'UnsupportedContentTypeError',

    # Processors
    'AudioProcessor',
    'DocumentProcessor',
    'ImageProcessor',
    'VideoProcessor',

    # Archives
    'ArchiveError',
    'ArchiveHandler',

    # Protected content
    'ProtectedContentError',
    'ProtectedContentHandler',

    # RAG integration
    'ContentRAGError',
    'ContentRAGProcessor',
] 