"""
Base classes for RAG processor plugins.

This module imports and re-exports the base classes for RAG processor plugins
from the framework.
"""

from pepperpy.plugin.rag.base import (
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

__all__ = [
    "ProcessedText",
    "ProcessingOptions",
    "TextProcessingError",
    "TextProcessor",
]
