"""Processing module for handling different types of content.

This module provides a unified interface for processing various types of content,
including text, code, markdown, JSON, YAML, and more. It includes a plugin system
for extending functionality and comprehensive monitoring capabilities.
"""

from pepperpy.processing.base import (
    BaseProcessor,
    ProcessingContext,
    ProcessingResult,
    ProcessorError,
)
from pepperpy.processing.factory import ProcessorFactory
from pepperpy.processing.registry import ProcessorRegistry
from pepperpy.processing.utils import ProcessingUtils

__all__ = [
    "BaseProcessor",
    "ProcessingContext",
    "ProcessingResult",
    "ProcessingUtils",
    "ProcessorError",
    "ProcessorFactory",
    "ProcessorRegistry",
]
