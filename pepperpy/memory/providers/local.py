"""Local file-based memory provider."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from pepperpy.memory.base import MemoryEntry, MemoryError, MemoryProvider


class LocalConfig(BaseModel):
    """Configuration for local memory provider."""

    path: Union[str, Path] = Field(
        default="~/.pepperpy/memory",
        description="Path to memory directory",
    )
    max_size: str = Field(
        default="1GB",
        description="Maximum storage size (e.g. '100MB', '1GB')",
    )
    sync_interval: float = Field(
        default=60.0,
        description="Interval in seconds to sync to disk",
    )
    compression: bool = Field(
        default=True,
        description="Whether to compress stored data",
    )


class LocalProvider(MemoryProvider):
    """Local file-based implementation of memory provider."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            MemoryError: If configuration is invalid
        """
        try:
            self.config = LocalConfig(**config)
            self.path = Path(self.config.path).expanduser()
            self.entries: Dict[str, MemoryEntry] = {}
            self._lock = asyncio.Lock()
            self._sync_task: Optional[asyncio.Task] = None
            self._modified = False
        except Exception as e:
            raise MemoryError(
                "Failed to initialize local provider",
                provider="local",
                details={"error": str(e)},
            )

    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            MemoryError: If initialization fails
        """
        try:
            # Create directory if needed
            self.path.mkdir(parents=True, exist_ok=True)

            # Load existing entries
            await self._load_entries()

            # Start sync task
            self._sync_task = asyncio.create_task(self._sync_loop())

        except Exception as e:
            raise MemoryError(
                "Failed to initialize local provider",
                provider="local",
                details={"error": str(e)},
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        # Final sync
        if self._modified:
            await self._sync_to_disk()

    async def get(
        self,
        key: str,
        *,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Get a value from memory.

        Args:
            key: Key to retrieve
            default: Default value if key doesn't exist
            **kwargs: Additional provider-specific parameters

        Returns:
            Stored value or default

        Raises:
            MemoryError: If retrieval fails
        """
        try:
            async with self._lock:
                entry = self.entries.get(key)
                if not entry:
                    return default

                # Check expiration
                if entry.expires_at and entry.expires_at <= datetime.now():
                    await self.delete(key)
                    return default

                return entry.value

        except Exception as e:
            raise MemoryError(
                "Failed to get value",
                provider="local",
                key=key,
                details={"error": str(e)},
            )

    async def set(
        self,
        key: str,
        value: Any,
        *,
        expires_in: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Set a value in memory.

        Args:
            key: Key to store
            value: Value to store
            expires_in: Optional expiration time in seconds
            metadata: Optional metadata to store
            **kwargs: Additional provider-specific parameters

        Raises:
            MemoryError: If storage fails
        """
        try:
            now = datetime.now()
            entry = MemoryEntry(
                key=key,
                value=value,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(seconds=expires_in) if expires_in else None,
                metadata=metadata or {},
            )

            async with self._lock:
                self.entries[key] = entry
                self._modified = True

        except Exception as e:
            raise MemoryError(
                "Failed to set value",
                provider="local",
                key=key,
                details={"error": str(e)},
            )

    async def delete(
        self,
        key: str,
        **kwargs: Any,
    ) -> bool:
        """Delete a value from memory.

        Args:
            key: Key to delete
            **kwargs: Additional provider-specific parameters

        Returns:
            True if key was deleted, False if it didn't exist

        Raises:
            MemoryError: If deletion fails
        """
        try:
            async with self._lock:
                if key in self.entries:
                    del self.entries[key]
                    self._modified = True
                    return True
                return False

        except Exception as e:
            raise MemoryError(
                "Failed to delete value",
                provider="local",
                key=key,
                details={"error": str(e)},
            )

    async def exists(
        self,
        key: str,
        **kwargs: Any,
    ) -> bool:
        """Check if a key exists in memory.

        Args:
            key: Key to check
            **kwargs: Additional provider-specific parameters

        Returns:
            True if key exists, False otherwise

        Raises:
            MemoryError: If check fails
        """
        try:
            async with self._lock:
                entry = self.entries.get(key)
                if not entry:
                    return False

                # Check expiration
                if entry.expires_at and entry.expires_at <= datetime.now():
                    await self.delete(key)
                    return False

                return True

        except Exception as e:
            raise MemoryError(
                "Failed to check key existence",
                provider="local",
                key=key,
                details={"error": str(e)},
            )

    async def clear(
        self,
        pattern: Optional[str] = None,
        **kwargs: Any,
    ) -> int:
        """Clear memory entries.

        Args:
            pattern: Optional pattern to match keys
            **kwargs: Additional provider-specific parameters

        Returns:
            Number of entries cleared

        Raises:
            MemoryError: If clearing fails
        """
        try:
            count = 0
            async with self._lock:
                if pattern:
                    keys_to_delete = [
                        key for key in self.entries if key.startswith(pattern)
                    ]
                    for key in keys_to_delete:
                        del self.entries[key]
                        count += 1
                else:
                    count = len(self.entries)
                    self.entries.clear()

                if count > 0:
                    self._modified = True

                return count

        except Exception as e:
            raise MemoryError(
                "Failed to clear entries",
                provider="local",
                details={"error": str(e)},
            )

    async def keys(
        self,
        pattern: Optional[str] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Get all keys in memory.

        Args:
            pattern: Optional pattern to match keys
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching keys

        Raises:
            MemoryError: If key retrieval fails
        """
        try:
            async with self._lock:
                if pattern:
                    return [
                        key
                        for key in self.entries
                        if key.startswith(pattern)
                        and not (
                            self.entries[key].expires_at
                            and self.entries[key].expires_at <= datetime.now()
                        )
                    ]
                return [
                    key
                    for key in self.entries
                    if not (
                        self.entries[key].expires_at
                        and self.entries[key].expires_at <= datetime.now()
                    )
                ]

        except Exception as e:
            raise MemoryError(
                "Failed to get keys",
                provider="local",
                details={"error": str(e)},
            )

    async def entries(
        self,
        pattern: Optional[str] = None,
        **kwargs: Any,
    ) -> List[MemoryEntry]:
        """Get all entries in memory.

        Args:
            pattern: Optional pattern to match keys
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching entries

        Raises:
            MemoryError: If entry retrieval fails
        """
        try:
            async with self._lock:
                if pattern:
                    return [
                        entry
                        for key, entry in self.entries.items()
                        if key.startswith(pattern)
                        and not (
                            entry.expires_at and entry.expires_at <= datetime.now()
                        )
                    ]
                return [
                    entry
                    for entry in self.entries.values()
                    if not (entry.expires_at and entry.expires_at <= datetime.now())
                ]

        except Exception as e:
            raise MemoryError(
                "Failed to get entries",
                provider="local",
                details={"error": str(e)},
            )

    async def _load_entries(self) -> None:
        """Load entries from disk.

        Raises:
            MemoryError: If loading fails
        """
        try:
            entries_file = self.path / "entries.json"
            if not entries_file.exists():
                return

            async with self._lock:
                data = json.loads(entries_file.read_text())
                self.entries = {
                    key: MemoryEntry(
                        key=key,
                        value=entry["value"],
                        created_at=datetime.fromisoformat(entry["created_at"]),
                        updated_at=datetime.fromisoformat(entry["updated_at"]),
                        expires_at=datetime.fromisoformat(entry["expires_at"])
                        if entry.get("expires_at")
                        else None,
                        metadata=entry.get("metadata", {}),
                    )
                    for key, entry in data.items()
                }

        except Exception as e:
            raise MemoryError(
                "Failed to load entries",
                provider="local",
                details={"error": str(e)},
            )

    async def _sync_to_disk(self) -> None:
        """Sync entries to disk.

        Raises:
            MemoryError: If syncing fails
        """
        try:
            entries_file = self.path / "entries.json"
            async with self._lock:
                data = {
                    key: {
                        "value": entry.value,
                        "created_at": entry.created_at.isoformat(),
                        "updated_at": entry.updated_at.isoformat(),
                        "expires_at": entry.expires_at.isoformat()
                        if entry.expires_at
                        else None,
                        "metadata": entry.metadata,
                    }
                    for key, entry in self.entries.items()
                }
                entries_file.write_text(json.dumps(data, indent=2))
                self._modified = False

        except Exception as e:
            raise MemoryError(
                "Failed to sync entries",
                provider="local",
                details={"error": str(e)},
            )

    async def _sync_loop(self) -> None:
        """Background task to periodically sync entries to disk."""
        while True:
            try:
                await asyncio.sleep(self.config.sync_interval)
                if self._modified:
                    await self._sync_to_disk()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue running
                print(f"Error in sync loop: {e}")  # TODO: Use proper logging
