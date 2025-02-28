"""Format handling functionality for PepperPy.

This module provides functionality for handling various data formats:
- Text: Plain text processing
- JSON: JavaScript Object Notation
- YAML: YAML Ain't Markup Language
- XML: Extensible Markup Language
- CSV: Comma-Separated Values
- HTML: HyperText Markup Language
- Markdown: Lightweight markup language
- Vector: Vector data formats
- Audio: Audio data formats
- Image: Image data formats

The module centralizes format handling to provide consistent interfaces
for working with different data formats throughout the framework.
"""

from pepperpy.core.common.utils.serialization import (
    CsvUtils,
    JsonUtils,
    SerializationUtils,
    XmlUtils,
    YamlUtils,
)
from pepperpy.formats.audio import AudioProcessor
from pepperpy.formats.base import FormatProcessor
from pepperpy.formats.csv import CSVProcessor
from pepperpy.formats.html import HTMLProcessor
from pepperpy.formats.image import ImageProcessor
from pepperpy.formats.text import TextProcessor
from pepperpy.formats.vector import VectorProcessor

# Re-export utility classes from serialization.py
# to maintain backward compatibility
from pepperpy.formats.formatters import (
    Formatter,
    JsonFormatter,
    TextFormatter,
    XmlFormatter,
    YamlFormatter,
)
from pepperpy.formats.parsers import (
    JsonParser,
    Parser,
    TextParser,
    XmlParser,
    YamlParser,
)

__all__ = [
    # Processors
    "FormatProcessor",
    "TextProcessor",
    "CSVProcessor",
    "HTMLProcessor",
    "AudioProcessor",
    "ImageProcessor",
    "VectorProcessor",
    
    # Parsers
    "Parser",
    "TextParser",
    "JsonParser",
    "YamlParser",
    "XmlParser",
    
    # Formatters
    "Formatter",
    "TextFormatter",
    "JsonFormatter",
    "YamlFormatter",
    "XmlFormatter",
    
    # Utils
    "SerializationUtils",
    "JsonUtils",
    "YamlUtils",
    "XmlUtils",
    "CsvUtils",
]
