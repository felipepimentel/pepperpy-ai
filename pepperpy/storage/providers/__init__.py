"""Provider implementations for storage capabilities.

This module contains implementations of various storage providers that integrate
with different storage systems and services, including:

- Local: Integration with local filesystem storage
- Cloud: Integration with cloud storage services (S3, GCS, Azure Blob)
- SQL: Integration with SQL database storage systems

These providers enable persistent data storage and retrieval across different
storage backends with a consistent interface.
"""

# Import all providers from this directory
from pepperpy.storage.providers.cloud import CloudStorageProvider
from pepperpy.storage.providers.local import LocalStorageProvider
from pepperpy.storage.providers.sql import SQLStorageProvider

__all__ = [
    "CloudStorageProvider",
    "LocalStorageProvider",
    "SQLStorageProvider",
]
