"""Storage module for PepperPy."""

from pepperpy.core.base import PepperpyError
from pepperpy.storage.base import (
    StorageError,
    StorageObject,
    StorageProvider,
    create_provider,
)
from pepperpy.storage.providers.local import LocalProvider

__all__ = [
    "StorageError",
    "StorageObject",
    "StorageProvider",
    "create_provider",
    "LocalProvider",
    "PepperpyError",
]
