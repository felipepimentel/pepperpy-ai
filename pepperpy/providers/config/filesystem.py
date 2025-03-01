"""Filesystem configuration provider.

This module provides a configuration provider that stores values in JSON files.
"""

import json
from datetime import datetime
from pathlib import Path

from pepperpy.core.common.config.base import ConfigProvider


class FilesystemProvider(ConfigProvider):
    """Configuration provider that stores values in JSON files.

    This provider stores configuration values in JSON files within a
    specified directory. Each configuration key maps to a file.
    """

    def __init__(self, directory: str | Path) -> None:
        """Initialize the provider.

        Args:
            directory: Directory to store configuration files in
        """
        super().__init__()
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, str] = {}
        self._last_read: dict[str, datetime] = {}

    def _get_path(self, key: str) -> Path:
        """Get path for configuration key.

        Args:
            key: Configuration key

        Returns:
            Path to configuration file
        """
        # Replace invalid characters
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.directory / f"{safe_key}.json"

    def _should_reload(self, key: str, path: Path) -> bool:
        """Check if configuration should be reloaded.

        Args:
            key: Configuration key
            path: Path to configuration file

        Returns:
            True if configuration should be reloaded
        """
        # Always reload if not in cache
        if key not in self._cache:
            return True

        # Check if file has been modified
        last_read = self._last_read.get(key)
        if last_read is None:
            return True

        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            return mtime > last_read
        except FileNotFoundError:
            return True

    async def get(self, key: str) -> str | None:
        """Get configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None if not found
        """
        path = self._get_path(key)

        try:
            # Check if we need to reload
            if self._should_reload(key, path):
                # Read and parse file
                with path.open() as f:
                    data = json.load(f)
                value = str(data["value"])

                # Update cache
                self._cache[key] = value
                self._last_read[key] = datetime.now()

                # Record metrics
                self._metrics.counter(
                    "config_filesystem_reads",
                    1,
                    labels={"key": key},
                )

            return self._cache.get(key)

        except FileNotFoundError:
            return None
        except Exception as e:
            self._observability.log_error(
                "config.filesystem.get",
                f"Failed to read configuration: {e}",
                exception=e,
                context={"key": key, "path": str(path)},
            )
            raise

    async def set(self, key: str, value: str) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        path = self._get_path(key)

        try:
            # Write file
            with path.open("w") as f:
                json.dump({"value": value}, f, indent=2)

            # Update cache
            self._cache[key] = value
            self._last_read[key] = datetime.now()

            # Record metrics
            self._metrics.counter(
                "config_filesystem_writes",
                1,
                labels={"key": key},
            )

        except Exception as e:
            self._observability.log_error(
                "config.filesystem.set",
                f"Failed to write configuration: {e}",
                exception=e,
                context={"key": key, "path": str(path)},
            )
            raise

    async def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key
        """
        path = self._get_path(key)

        try:
            # Delete file
            path.unlink(missing_ok=True)

            # Update cache
            self._cache.pop(key, None)
            self._last_read.pop(key, None)

            # Record metrics
            self._metrics.counter(
                "config_filesystem_deletes",
                1,
                labels={"key": key},
            )

        except Exception as e:
            self._observability.log_error(
                "config.filesystem.delete",
                f"Failed to delete configuration: {e}",
                exception=e,
                context={"key": key, "path": str(path)},
            )
            raise

    async def list(self, prefix: str = "") -> list[str]:
        """List configuration keys.

        Args:
            prefix: Optional key prefix to filter by

        Returns:
            List of configuration keys
        """
        try:
            # Get all JSON files
            paths = self.directory.glob("*.json")

            # Convert to keys
            keys = []
            for path in paths:
                key = path.stem.replace("_", "/")
                if key.startswith(prefix):
                    keys.append(key)

            # Record metrics
            self._metrics.gauge(
                "config_filesystem_keys",
                len(keys),
                labels={"prefix": prefix},
            )

            return sorted(keys)

        except Exception as e:
            self._observability.log_error(
                "config.filesystem.list",
                f"Failed to list configuration: {e}",
                exception=e,
                context={"prefix": prefix},
            )
            raise


# Alias for backward compatibility
FilesystemConfigProvider = FilesystemProvider
