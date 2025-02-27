"""Unified format handling system for PepperPy.

This module provides a unified system for handling various data formats:
- Base functionality: Common interfaces and abstractions
- Text formats: Plain text, Markdown, JSON, YAML, XML
- Audio formats: WAV, MP3, FLAC, OGG
- Image formats: PNG, JPEG, GIF, BMP, TIFF
- Vector formats: NumPy arrays, JSON vectors, binary vectors, FAISS indices

All components should utilize this module for their format handling needs,
with appropriate specialization for specific requirements.
"""

from typing import Dict, List, Optional, Type, Union

# Import base classes
from .base import FormatError, FormatHandler, FormatRegistry

# Create a global format registry
_registry = FormatRegistry()


# Format handler getter functions
def get_format_by_extension(extension: str) -> Optional[FormatHandler]:
    """Get a format handler by file extension.

    Args:
        extension: File extension (without dot)

    Returns:
        Format handler or None if not found
    """
    return _registry.get_by_extension(extension)


def get_format_by_mime_type(mime_type: str) -> Optional[FormatHandler]:
    """Get a format handler by MIME type.

    Args:
        mime_type: MIME type string

    Returns:
        Format handler or None if not found
    """
    return _registry.get_by_mime_type(mime_type)


def register_format(format_handler: FormatHandler) -> None:
    """Register a format handler.

    Args:
        format_handler: Format handler to register
    """
    _registry.register(format_handler)


def _register_default_formats() -> None:
    """Register default format handlers."""
    # This function will be called when the formats are imported
    # It will register all the default format handlers

    # Import format handlers
    try:
        from .text import (
            JSONFormat,
            MarkdownFormat,
            PlainTextFormat,
            XMLFormat,
            YAMLFormat,
        )

        register_format(PlainTextFormat())
        register_format(MarkdownFormat())
        register_format(JSONFormat())
        register_format(YAMLFormat())
        register_format(XMLFormat())
    except ImportError:
        pass  # Text formats not available

    try:
        from .audio import FLACFormat, MP3Format, OGGFormat, WAVFormat

        register_format(WAVFormat())
        register_format(MP3Format())
        register_format(FLACFormat())
        register_format(OGGFormat())
    except ImportError:
        pass  # Audio formats not available

    try:
        from .image import BMPFormat, GIFFormat, JPEGFormat, PNGFormat, TIFFFormat

        register_format(PNGFormat())
        register_format(JPEGFormat())
        register_format(GIFFormat())
        register_format(BMPFormat())
        register_format(TIFFFormat())
    except ImportError:
        pass  # Image formats not available

    try:
        from .vector import (
            BinaryVectorFormat,
            FaissIndexFormat,
            JSONVectorFormat,
            NumpyFormat,
        )

        register_format(NumpyFormat())
        register_format(JSONVectorFormat())
        register_format(BinaryVectorFormat())
        register_format(FaissIndexFormat())
    except ImportError:
        pass  # Vector formats not available


# Register default formats when the module is imported
_register_default_formats()

# Public API
__all__ = [
    "FormatError",
    "FormatHandler",
    "FormatRegistry",
    "get_format_by_extension",
    "get_format_by_mime_type",
    "register_format",
]
