"""Utilities for configuration file manipulation.

Implements helper functions for manipulating and formatting configuration files.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils.json import JsonUtils
from pepperpy.core.utils.yaml import YamlUtils


class ConfigUtils:
    """Utility functions for configuration manipulation."""

    @staticmethod
    def load(path: Union[str, Path], format: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            path: File path
            format: File format (json, yaml)

        Returns:
            Configuration dictionary
        """
        path = Path(path)
        if format is None:
            format = path.suffix.lstrip(".")

        if format == "json":
            return JsonUtils.load(path)
        elif format in ("yaml", "yml"):
            return YamlUtils.load(path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def save(
        data: Dict[str, Any], path: Union[str, Path], format: Optional[str] = None
    ) -> None:
        """Save configuration to file.

        Args:
            data: Configuration dictionary
            path: File path
            format: File format (json, yaml)
        """
        path = Path(path)
        if format is None:
            format = path.suffix.lstrip(".")

        if format == "json":
            JsonUtils.save(data, path)
        elif format in ("yaml", "yml"):
            YamlUtils.save(data, path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def get_config_path(
        name: str,
        search_paths: Optional[List[Union[str, Path]]] = None,
        formats: Optional[List[str]] = None,
    ) -> Optional[Path]:
        """Find configuration file in search paths.

        Args:
            name: Configuration name
            search_paths: Paths to search
            formats: File formats to search

        Returns:
            Configuration file path or None
        """
        if search_paths is None:
            search_paths = [Path.cwd(), Path.home() / ".config", Path("/etc")]

        if formats is None:
            formats = ["json", "yaml", "yml"]

        for path in search_paths:
            path = Path(path)
            if not path.exists():
                continue

            for fmt in formats:
                config_path = path / f"{name}.{fmt}"
                if config_path.exists():
                    return config_path

        return None

    @staticmethod
    def load_env_vars(prefix: str = "", lowercase: bool = True) -> Dict[str, str]:
        """Load environment variables with prefix.

        Args:
            prefix: Variable prefix
            lowercase: Whether to lowercase keys

        Returns:
            Dictionary of environment variables
        """
        result = {}
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue

            if prefix:
                key = key[len(prefix) :]

            if lowercase:
                key = key.lower()

            result[key] = value

        return result

    @staticmethod
    def merge_configs(*configs: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Merge multiple configurations.

        Args:
            *configs: Configurations to merge
            deep: Whether to perform deep merge

        Returns:
            Merged configuration
        """
        result: Dict[str, Any] = {}

        for config in configs:
            if not deep:
                result.update(config)
            else:
                for key, value in config.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        result[key] = ConfigUtils.merge_configs(
                            result[key], value, deep=True
                        )
                    else:
                        result[key] = value

        return result

    @staticmethod
    def get_nested(
        config: Dict[str, Any], path: str, default: Any = None, separator: str = "."
    ) -> Any:
        """Get nested configuration value.

        Args:
            config: Configuration dictionary
            path: Value path
            default: Default value
            separator: Path separator

        Returns:
            Configuration value
        """
        current = config
        for key in path.split(separator):
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is None:
                return default
        return current

    @staticmethod
    def set_nested(
        config: Dict[str, Any], path: str, value: Any, separator: str = "."
    ) -> None:
        """Set nested configuration value.

        Args:
            config: Configuration dictionary
            path: Value path
            value: Value to set
            separator: Path separator
        """
        keys = path.split(separator)
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def flatten(
        config: Dict[str, Any], parent_key: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested configuration.

        Args:
            config: Configuration dictionary
            parent_key: Parent key
            separator: Key separator

        Returns:
            Flattened configuration
        """
        items: List[tuple[str, Any]] = []

        for key, value in config.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    ConfigUtils.flatten(value, new_key, separator=separator).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    @staticmethod
    def unflatten(config: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Unflatten configuration with dot notation keys.

        Args:
            config: Flattened configuration
            separator: Key separator

        Returns:
            Nested configuration
        """
        result: Dict[str, Any] = {}

        for key, value in config.items():
            ConfigUtils.set_nested(result, key, value, separator)

        return result
