"""
PepperPy RAG (Retrieval-Augmented Generation) Module.

This module provides core functionality for RAG pipelines.
"""

from pepperpy.rag.processor import (
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
