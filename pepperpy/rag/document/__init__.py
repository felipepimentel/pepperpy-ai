"""Document module for RAG.

This module provides functionality for working with documents in RAG,
including loading, processing, and transformation.
"""

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
from pepperpy.rag.models import Document, DocumentChunk, Metadata

__all__ = [
    # Core document models imported from models.py
    "Document",
    "DocumentChunk",
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
]
