"""Data module for managing data ingestion, transformation, and storage.

This module provides functionality for handling dynamic data sources,
document storage, and data transformation pipelines.
"""

from .dynamic_sources import (
    DocumentStore,
    DocumentStoreError,
    Document,
    DocumentMetadata,
    DynamicSource,
    DynamicSourceError,
)


__all__ = [
    # Document storage
    "DocumentStore",
    "DocumentStoreError",
    "Document",
    "DocumentMetadata",
    # Dynamic sources
    "DynamicSource",
    "DynamicSourceError",
]
