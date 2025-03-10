"""Document loaders module.

This module provides functionality for loading documents from various sources.
"""

from pepperpy.rag.document.loaders.base import BaseDocumentLoader
from pepperpy.rag.document.loaders.csv import CSVLoader
from pepperpy.rag.document.loaders.html import HTMLLoader
from pepperpy.rag.document.loaders.pdf import PDFLoader
from pepperpy.rag.document.loaders.text import TextLoader

__all__ = [
    "BaseDocumentLoader",
    "TextLoader",
    "PDFLoader",
    "HTMLLoader",
    "CSVLoader",
]
