"""Storage System for PepperPy

This module provides a unified storage system for the PepperPy framework,
supporting various storage backends including:
- Local filesystem
- Cloud storage (AWS S3, Google Cloud Storage, etc.)
- SQL databases
- NoSQL databases

It provides a consistent interface for storing and retrieving data
regardless of the underlying storage technology.
"""

# Re-export from providers.storage for backward compatibility
from pepperpy.providers.storage import *
from pepperpy.storage.base import StorageError, StorageProvider

__all__ = [
    "StorageProvider",
    "StorageError",
]
