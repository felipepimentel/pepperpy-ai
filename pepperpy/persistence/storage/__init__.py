"""Storage module for Pepperpy framework.

This module provides storage implementations for different backends
and data formats.
"""

from pepperpy.persistence.storage.document import Document, DocumentStore, DocumentError

__all__ = [
    "Document",
    "DocumentStore",
    "DocumentError",
]
