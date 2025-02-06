"""Memory system exceptions.

This module defines exceptions specific to the memory management system.
"""


class MemoryError(Exception):
    """Base class for memory system exceptions."""


class MemoryBackendError(MemoryError):
    """Exception raised when a memory backend operation fails."""


class MemoryStorageError(MemoryBackendError):
    """Exception raised when storing data in memory fails."""


class MemoryRetrievalError(MemoryBackendError):
    """Exception raised when retrieving data from memory fails."""


class MemoryDeletionError(MemoryBackendError):
    """Exception raised when deleting data from memory fails."""


class MemoryExistsError(MemoryBackendError):
    """Exception raised when checking key existence in memory fails."""


class MemoryCleanupError(MemoryBackendError):
    """Exception raised when cleaning up memory resources fails."""


class MemoryBackendNotFoundError(MemoryError):
    """Exception raised when a requested memory backend is not found."""


class MemoryBackendAlreadyExistsError(MemoryError):
    """Exception raised when registering a memory backend that already exists."""


class MemoryBackendInvalidError(MemoryError):
    """Exception raised when a memory backend does not implement required interface."""
