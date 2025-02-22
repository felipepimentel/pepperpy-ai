"""Simple in-memory storage implementation."""

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

from pepperpy.core.resources import Resource
from pepperpy.memory.errors import (
    MemoryCleanupError,
    MemoryError,
    MemoryInitError,
    MemoryKeyError,
    MemoryStorageError,
)


class SimpleMemory(Resource):
    """Simple in-memory storage implementation with automatic cleanup."""

    def __init__(
        self,
        auto_cleanup: bool = True,
        cleanup_interval: Optional[int] = None,
        max_entries: int = 10000,
        default_expiration: int = 86400,
        **kwargs: Any,
    ) -> None:
        """Initialize memory.

        Args:
            auto_cleanup: Whether to automatically clean up expired entries
            cleanup_interval: Interval in seconds for cleanup
            max_entries: Maximum number of entries to store
            default_expiration: Default expiration time in seconds
            **kwargs: Additional configuration options
        """
        super().__init__(
            auto_cleanup=auto_cleanup,
            cleanup_interval=cleanup_interval,
        )
        self._store: Dict[str, Dict[str, Any]] = {}
        self._max_entries = max_entries
        self._default_expiration = default_expiration

    async def _initialize(self) -> None:
        """Initialize memory storage.

        Raises:
            MemoryInitError: If initialization fails
        """
        try:
            self._store.clear()
        except Exception as e:
            raise MemoryInitError(f"Failed to initialize memory: {e}")

    async def _cleanup(self) -> None:
        """Clean up expired entries.

        Raises:
            MemoryCleanupError: If cleanup fails
        """
        try:
            now = datetime.now(UTC)
            expired = [
                key
                for key, entry in self._store.items()
                if entry.get("expires_at") and entry["expires_at"] <= now
            ]
            for key in expired:
                del self._store[key]
        except Exception as e:
            raise MemoryCleanupError(f"Failed to clean up memory: {e}")

    async def store(
        self,
        key: str,
        value: Any,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Store value in memory.

        Args:
            key: Key to store value under
            value: Value to store
            expires_at: Optional expiration time

        Raises:
            MemoryStorageError: If storage fails or max entries exceeded
            MemoryError: If memory not initialized
        """
        if not self._initialized:
            raise MemoryError("Memory not initialized")

        try:
            # Check max entries limit
            if len(self._store) >= self._max_entries and key not in self._store:
                raise MemoryStorageError(
                    f"Max entries limit reached: {self._max_entries}"
                )

            # Use default expiration if none provided
            if expires_at is None and self._default_expiration:
                expires_at = datetime.now(UTC) + timedelta(
                    seconds=self._default_expiration
                )

            self._store[key] = {
                "value": value,
                "created_at": datetime.now(UTC),
                "expires_at": expires_at,
            }
        except Exception as e:
            raise MemoryStorageError(f"Failed to store memory entry: {e}")

    async def retrieve(
        self,
        key: str,
    ) -> Any:
        """Retrieve value from memory.

        Args:
            key: Key to retrieve value for

        Returns:
            Stored value

        Raises:
            MemoryKeyError: If key not found or expired
            MemoryError: If retrieval fails or memory not initialized
        """
        if not self._initialized:
            raise MemoryError("Memory not initialized")

        try:
            if key not in self._store:
                raise MemoryKeyError(f"Key not found: {key}")

            entry = self._store[key]

            # Check expiration
            if entry.get("expires_at") and entry["expires_at"] <= datetime.now(UTC):
                del self._store[key]
                raise MemoryKeyError(f"Key expired: {key}")

            return entry["value"]

        except MemoryKeyError:
            raise
        except Exception as e:
            raise MemoryError(f"Failed to retrieve memory entry: {e}")

    async def process(self, input: str) -> str:
        """Process memory operation.

        This method is required by the Resource interface but not used
        in this implementation.

        Args:
            input: Input text to process

        Returns:
            Empty string as this operation is not supported

        Raises:
            NotImplementedError: This operation is not supported
        """
        raise NotImplementedError("Memory resources do not support direct processing")
