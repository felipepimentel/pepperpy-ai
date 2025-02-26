"""Configuration utilities for Pepperpy.

This module provides utility functions for:
- Loading and saving configuration files
- Managing configuration directories
- Configuration validation
"""

import json
import os
from pathlib import Path
from typing import Any

import click

from pepperpy.core.errors.errors import ConfigError, ValidationError


def validate_path(path: str | Path, must_exist: bool = True) -> Path:
    """Validate and convert a path string.

    Args:
        path: The path to validate.
        must_exist: Whether the path must exist.

    Returns:
        The validated Path object.

    Raises:
        ValidationError: If the path is invalid or doesn't exist when required.
    """
    try:
        path_obj = Path(path).resolve()
        if must_exist and not path_obj.exists():
            raise ValidationError("path", str(path), "Path does not exist")
        return path_obj
    except Exception as e:
        raise ValidationError("path", str(path), str(e))


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load and validate a JSON configuration file.

    Args:
        config_path: Path to the config file.

    Returns:
        The loaded configuration dictionary.

    Raises:
        ConfigError: If the config file is invalid or cannot be loaded.
    """
    try:
        path_obj = validate_path(config_path)
        with path_obj.open() as f:
            return json.load(f)
    except ValidationError as e:
        raise ConfigError(str(config_path), str(e))
    except json.JSONDecodeError as e:
        raise ConfigError(str(config_path), f"Invalid JSON: {e!s}")
    except Exception as e:
        raise ConfigError(str(config_path), str(e))


def save_config(config: dict[str, Any], config_path: str | Path) -> None:
    """Save a configuration dictionary to a JSON file.

    Args:
        config: The configuration dictionary to save.
        config_path: Path to save the config file.

    Raises:
        ConfigError: If the config cannot be saved.
    """
    try:
        path_obj = Path(config_path)
        with path_obj.open("w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise ConfigError(str(config_path), f"Failed to save config: {e!s}")


def get_config_dir() -> Path:
    """Get the Pepperpy configuration directory.

    Returns:
        Path to the config directory.
    """
    config_dir = Path(click.get_app_dir("pepperpy"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get the Pepperpy data directory.

    Returns:
        Path to the data directory.
    """
    data_dir = Path(os.path.expanduser("~/.local/share/pepperpy"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
