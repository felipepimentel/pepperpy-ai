"""Storage providers for pepperpy.

This module contains storage providers for pepperpy, including:
- Local file system storage
- Cloud storage (S3, GCS, etc.)
- SQL database storage
"""

from typing import Dict, Type

from pepperpy.storage.base import StorageProvider

# Registry of available storage providers
STORAGE_PROVIDERS: Dict[str, Type[StorageProvider]] = {}


def register_storage_provider(name: str, provider: Type[StorageProvider]) -> None:
    """Register a storage provider.

    Args:
        name: Provider name
        provider: Provider class
    """
    STORAGE_PROVIDERS[name] = provider


__all__ = [
    "register_storage_provider",
    "STORAGE_PROVIDERS",
]
