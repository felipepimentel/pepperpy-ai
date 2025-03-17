"""Core functionality for PepperPy.

This module provides core functionality used throughout the PepperPy framework.
It includes utilities for working with the file system, configuration, and logging.
"""

import os
import platform
from pathlib import Path
from typing import Optional, Union

from pepperpy.core.errors import PepperPyError


class ServiceUnavailableError(PepperPyError):
    """Error raised when a service is unavailable."""

    pass


class TimeoutError(PepperPyError):
    """Error raised when an operation times out."""

    pass


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to the project root directory
    """
    # Try to find the root by looking for setup.py or pyproject.toml
    cwd = Path.cwd()
    for path in [cwd] + list(cwd.parents):
        if (path / "setup.py").exists() or (path / "pyproject.toml").exists():
            return path

    # If we can't find the root, use the current working directory
    return cwd


def get_data_dir() -> Path:
    """Get the data directory for the application.

    Returns:
        Path to the data directory
    """
    root = get_project_root()
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_output_dir() -> Path:
    """Get the output directory for the application.

    Returns:
        Path to the output directory
    """
    root = get_project_root()
    output_dir = root / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_config_dir() -> Path:
    """Get the configuration directory for the application.

    Returns:
        Path to the configuration directory
    """
    # If we're on Linux, use the XDG config dir
    if platform.system() == "Linux":
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")) / "pepperpy"
    # If we're on macOS, use the Application Support directory
    elif platform.system() == "Darwin":
        config_dir = Path("~/Library/Application Support/PepperPy").expanduser()
    # If we're on Windows, use the AppData directory
    elif platform.system() == "Windows":
        config_dir = Path(os.environ.get("APPDATA", "~\\AppData\\Roaming")) / "PepperPy"
    # Otherwise, use a .pepperpy directory in the user's home directory
    else:
        config_dir = Path("~/.pepperpy").expanduser()

    config_dir.mkdir(exist_ok=True, parents=True)
    return config_dir


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure that a directory exists.

    Args:
        path: Path to the directory

    Returns:
        Path object for the directory
    """
    if isinstance(path, str):
        path = Path(path)

    path.mkdir(exist_ok=True, parents=True)
    return path


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable.

    Args:
        name: Name of the environment variable
        default: Default value to return if the variable is not set

    Returns:
        Value of the environment variable, or the default value if not set
    """
    return os.environ.get(name, default)
