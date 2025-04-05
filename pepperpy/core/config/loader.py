"""
Configuration Loader.

This module provides utilities for loading configuration from various sources,
including YAML files, JSON files, and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Any

import yaml

from pepperpy.core.config.schema import PepperPyConfig, resolve_env_references
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Standard config file locations to search
CONFIG_SEARCH_PATHS = [
    "config.yaml",
    "config.yml",
    "config/config.yaml",
    "config/config.yml",
    "conf/config.yaml",
    "conf/config.yml",
    "pepperpy.yaml",
    "pepperpy.yml",
]


def load_config(path: str | Path) -> dict[str, Any]:
    """Load configuration from a file.

    Supports JSON and YAML formats, detected by file extension.

    Args:
        path: Path to the configuration file

    Returns:
        Loaded configuration as a dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    # Determine format from extension
    suffix = path_obj.suffix.lower()

    if suffix in (".yaml", ".yml"):
        return load_yaml(path_obj)
    elif suffix == ".json":
        return load_json(path_obj)
    else:
        raise ValueError(f"Unsupported configuration format: {suffix}")


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML configuration file.

    Args:
        path: Path to the YAML file

    Returns:
        Loaded configuration as a dictionary

    Raises:
        Exception: If there's an error loading the file
    """
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading YAML configuration: {e}")
        raise


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON configuration file.

    Args:
        path: Path to the JSON file

    Returns:
        Loaded configuration as a dictionary

    Raises:
        Exception: If there's an error loading the file
    """
    try:
        with open(path) as f:
            return json.load(f) or {}
    except Exception as e:
        logger.error(f"Error loading JSON configuration: {e}")
        raise


def get_env_config(prefix: str = "PEPPERPY_") -> dict[str, Any]:
    """Get configuration from environment variables.

    Environment variables can define nested configuration using double
    underscores as separators. For example, PEPPERPY_LLM__MODEL will be
    converted to {"llm": {"model": <value>}}.

    Args:
        prefix: Prefix for environment variables to include

    Returns:
        Configuration dictionary from environment variables
    """
    result: dict[str, Any] = {}

    # Filter environment variables with the given prefix
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        # Remove prefix and split into parts
        config_key = key[len(prefix) :]
        if not config_key:
            continue

        # Convert to lowercase for consistency
        config_key = config_key.lower()

        # Handle nested keys using double underscore as separator
        parts = config_key.split("__")

        # Build nested dictionary
        current = result
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Last part is the final key
                current[part] = _convert_env_value(value)
            else:
                # Create nested dictionary if needed
                if part not in current:
                    current[part] = {}
                current = current[part]

    return result


def _convert_env_value(value: str) -> str | int | float | bool | None:
    """Convert environment variable string to appropriate type.

    Args:
        value: String value from environment variable

    Returns:
        Converted value
    """
    # Handle special string values
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    elif value.lower() == "null" or value.lower() == "none":
        return None

    # Try converting to number
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        # Keep as string if not a number
        return value


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Later configurations take precedence over earlier ones,
    with nested dictionaries being merged recursively.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration dictionary
    """
    if not configs:
        return {}

    # Start with the first config
    result = dict(configs[0])

    # Merge each subsequent config
    for config in configs[1:]:
        _recursive_update(result, config)

    return result


def _recursive_update(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Recursively update a dictionary.

    Args:
        target: Target dictionary to update
        source: Source dictionary with updates
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Recursively update nested dictionaries
            _recursive_update(target[key], value)
        else:
            # Replace or add value
            target[key] = value


def load_yaml_config(file_path: str | Path) -> PepperPyConfig:
    """Load and validate YAML configuration file.

    This function loads a YAML configuration file, resolves environment
    variables, and validates it against the schema.

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        Validated PepperPyConfig object

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValidationError: If the configuration is invalid
    """
    # Load raw configuration
    raw_config = load_yaml(Path(file_path))

    # Resolve environment variable references
    resolved_config = resolve_env_references(raw_config)

    # Create and validate configuration object
    try:
        return PepperPyConfig(**resolved_config)
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        from pepperpy.core.errors import ValidationError

        raise ValidationError(
            f"Invalid configuration in {file_path}: {e}", errors=[str(e)]
        )


def find_config_file() -> Path | None:
    """Find configuration file in standard locations.

    This function searches for a configuration file in standard locations,
    including the current directory, config/ subdirectory, etc.

    Returns:
        Path to the configuration file if found, None otherwise
    """
    # Check environment variable first
    env_path = os.environ.get("PEPPERPY_CONFIG_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        logger.warning(
            f"Configuration file specified in PEPPERPY_CONFIG_PATH not found: {env_path}"
        )

    # Check standard paths relative to current directory
    for path_str in CONFIG_SEARCH_PATHS:
        path = Path(path_str)
        if path.exists():
            return path

    # Check in the package directory if running as a module
    try:
        package_dir = Path(__file__).parent.parent.parent
        for path_str in CONFIG_SEARCH_PATHS:
            path = package_dir / path_str
            if path.exists():
                return path
    except Exception:
        pass

    # No configuration file found
    return None
