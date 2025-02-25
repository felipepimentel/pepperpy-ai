"""Environment configuration module for PepperPy.

This module provides functionality for loading configuration from environment variables.
"""

import os
from typing import Any

from .base import ConfigProvider


class EnvConfigProvider(ConfigProvider):
    """Environment variable configuration provider.

    This provider loads configuration from environment variables.
    Environment variables are mapped to configuration keys using a prefix
    and separator. For example, with prefix "PEPPERPY" and separator "_",
    the environment variable "PEPPERPY_DATABASE_URL" would map to the
    configuration key "database.url".
    """

    def __init__(
        self,
        prefix: str = "PEPPERPY",
        separator: str = "_",
        lowercase: bool = True,
    ) -> None:
        """Initialize provider.

        Args:
            prefix: Environment variable prefix.
            separator: Environment variable separator.
            lowercase: Convert keys to lowercase.
        """
        self._prefix = prefix
        self._separator = separator
        self._lowercase = lowercase
        self._cache: dict[str, Any] = {}
        self._load_env()

    def get(self, key: str) -> Any | None:
        """Get configuration value by key.

        Args:
            key: Configuration key.

        Returns:
            Configuration value or None if not found.
        """
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.

        Note:
            This operation only updates the cache, not the environment variables.
        """
        self._cache[key] = value

    def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key.

        Note:
            This operation only updates the cache, not the environment variables.
        """
        self._cache.pop(key, None)

    def exists(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key.

        Returns:
            True if key exists, False otherwise.
        """
        return key in self._cache

    def clear(self) -> None:
        """Clear all configuration values.

        Note:
            This operation only clears the cache, not the environment variables.
        """
        self._cache.clear()
        self._load_env()

    def _load_env(self) -> None:
        """Load configuration from environment variables."""
        prefix_len = len(self._prefix)
        for key, value in os.environ.items():
            if key.startswith(f"{self._prefix}{self._separator}"):
                # Remove prefix and convert separators to dots
                config_key = key[prefix_len + 1 :].replace(self._separator, ".")
                if self._lowercase:
                    config_key = config_key.lower()

                # Convert value type if possible
                self._cache[config_key] = self._convert_value(value)

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type.

        Args:
            value: String value to convert.

        Returns:
            Converted value.
        """
        # Try to convert to boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass

        # Try to convert to list
        if value.startswith("[") and value.endswith("]"):
            try:
                items = [item.strip() for item in value[1:-1].split(",")]
                return [self._convert_value(item) for item in items if item]
            except Exception:
                pass

        # Return as string
        return value
