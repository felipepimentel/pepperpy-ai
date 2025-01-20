"""Document store module for Pepperpy."""

from .base import Document, DocumentStore
from .sqlite import SQLiteDocumentStore

__all__ = [
    "Document",
    "DocumentStore",
    "SQLiteDocumentStore",
] 