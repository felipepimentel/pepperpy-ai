"""
PepperPy RAG Document Module.

Este módulo contém as classes e funções para trabalhar com documentos no sistema RAG.
"""

from __future__ import annotations

from pepperpy.rag.document.core import Document, Metadata
from pepperpy.rag.document.loaders import (
    CSVLoader,
    DocumentLoader,
    HTMLLoader,
    PDFLoader,
    TextLoader,
)
from pepperpy.rag.document.processors import (
    DocumentProcessor,
    HTMLProcessor,
    LanguageProcessor,
    MarkdownProcessor,
    MetadataProcessor,
    TextChunker,
    TextCleaner,
)
from pepperpy.rag.document.utils import (
    calculate_text_statistics,
    clean_markdown_formatting,
    clean_text,
    extract_html_metadata,
    remove_html_tags,
    split_text_by_char,
    split_text_by_separator,
)

__all__ = [
    # Core
    "Document",
    "Metadata",
    # Loaders
    "DocumentLoader",
    "TextLoader",
    "CSVLoader",
    "PDFLoader",
    "HTMLLoader",
    # Processors
    "DocumentProcessor",
    "TextChunker",
    "TextCleaner",
    "HTMLProcessor",
    "MarkdownProcessor",
    "LanguageProcessor",
    "MetadataProcessor",
    # Utils
    "calculate_text_statistics",
    "clean_markdown_formatting",
    "clean_text",
    "extract_html_metadata",
    "remove_html_tags",
    "split_text_by_char",
    "split_text_by_separator",
]
