"""File-based configuration provider."""

import json
from pathlib import Path
from typing import Dict, Optional

from pepperpy.core.common.config.providers.base import ConfigProvider
from pepperpy.core.common.config.types import ConfigValue


class FileConfigProvider(ConfigProvider):
    """Configuration provider that stores values in a JSON file."""

    def __init__(self, file_path: str):
        """Initialize the file config provider.

        Args:
            file_path: Path to the configuration file

        """
        self.file_path = Path(file_path)
        self._config: Dict[str, ConfigValue] = {}
        self._ensure_file_exists()
        self.load()

    def _ensure_file_exists(self) -> None:
        """Ensure the configuration file exists."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.save()

    def get(self, key: str) -> Optional[ConfigValue]:
        """Retrieve a configuration value by key."""
        return self._config.get(key)

    def set(self, key: str, value: ConfigValue) -> None:
        """Set a configuration value."""
        self._config[key] = value
        self.save()

    def delete(self, key: str) -> bool:
        """Delete a configuration value."""
        if key in self._config:
            del self._config[key]
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Clear all configuration values."""
        self._config.clear()
        self.save()

    def load(self) -> Dict[str, ConfigValue]:
        """Load all configuration values from file."""
        try:
            if self.file_path.exists():
                with open(self.file_path, encoding="utf-8") as f:
                    self._config = json.load(f)
        except (json.JSONDecodeError, OSError):
            # If file is corrupted or can't be read, start with empty config
            self._config = {}
        return self._config

    def save(self) -> None:
        """Save all configuration values to file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
        except OSError as e:
            raise RuntimeError(f"Failed to save configuration: {e}") from e

    def exists(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return key in self._config

    def get_namespace(self, namespace: str) -> Dict[str, ConfigValue]:
        """Get all configuration values under a namespace."""
        return {k: v for k, v in self._config.items() if k.startswith(f"{namespace}.")}
