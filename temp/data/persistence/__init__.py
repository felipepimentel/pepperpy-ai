"""Persistence module.

This module provides functionality for data persistence.
"""

from pepperpy.data.persistence.core import (
    FileStorageProvider,
    MemoryStorageProvider,
    StorageProvider,
    StorageProviderRegistry,
    StorageType,
    clear,
    clear_providers,
    connect,
    delete,
    disconnect,
    exists,
    get,
    get_provider,
    get_registry,
    is_connected,
    keys,
    list_providers,
    register_file_provider,
    register_memory_provider,
    register_provider,
    set,
    set_registry,
    unregister_provider,
)

__all__ = [
    "FileStorageProvider",
    "MemoryStorageProvider",
    "StorageProvider",
    "StorageProviderRegistry",
    "StorageType",
    "clear",
    "clear_providers",
    "connect",
    "delete",
    "disconnect",
    "exists",
    "get",
    "get_provider",
    "get_registry",
    "is_connected",
    "keys",
    "list_providers",
    "register_file_provider",
    "register_memory_provider",
    "register_provider",
    "set",
    "set_registry",
    "unregister_provider",
]
