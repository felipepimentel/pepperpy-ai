"""Content module for the Pepperpy framework.

This module provides functionality for managing and processing content:
- Content loading and validation
- Content transformation
- Content storage and retrieval
- Content metadata management
"""

from pepperpy.content.base import (
    Content,
    ContentConfig,
    ContentMetadata,
    ContentType,
)
from pepperpy.content.loaders import (
    ContentLoader,
    FileContent,
    FileContentLoader,
    TextContent,
    TextContentLoader,
)
from pepperpy.content.processors import (
    ContentProcessor,
    TextAnalyzer,
    TextProcessor,
)
from pepperpy.content.storage import (
    ContentStorage,
    LocalContentStorage,
)

__all__ = [
    # Base types
    "Content",
    "ContentConfig",
    "ContentMetadata",
    "ContentType",
    # Loaders
    "ContentLoader",
    "FileContent",
    "FileContentLoader",
    "TextContent",
    "TextContentLoader",
    # Processors
    "ContentProcessor",
    "TextAnalyzer",
    "TextProcessor",
    # Storage
    "ContentStorage",
    "LocalContentStorage",
]
