"""Core functionality for PepperPy.

This module defines the core abstractions and implementations for PepperPy.
It provides the foundation for all other modules in the framework.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional, Union

# Configure root logger with a basic format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Now using get_logger from utils module instead
# See pepperpy.utils.logging for the implementation


class PepperPyError(Exception):
    """Base class for all PepperPy exceptions.

    All exceptions in the PepperPy framework should inherit from this class.
    """

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.message = message
        self.details = kwargs
        super().__init__(message, *args)

    def __str__(self) -> str:
        """Get a string representation of the exception.

        Returns:
            A string representation
        """
        return self.message


class ConfigurationError(PepperPyError):
    """Raised when there is an error in the configuration."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "CONFIGURATION_ERROR")
        super().__init__(message, *args, **kwargs)


class ValidationError(PepperPyError):
    """Raised when validation fails."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "VALIDATION_ERROR")
        super().__init__(message, *args, **kwargs)


class ResourceNotFoundError(PepperPyError):
    """Raised when a resource is not found."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "RESOURCE_NOT_FOUND")
        super().__init__(message, *args, **kwargs)


class AuthenticationError(PepperPyError):
    """Raised when authentication fails."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "AUTHENTICATION_ERROR")
        super().__init__(message, *args, **kwargs)


class AuthorizationError(PepperPyError):
    """Raised when authorization fails."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "AUTHORIZATION_ERROR")
        super().__init__(message, *args, **kwargs)


class TimeoutError(PepperPyError):
    """Raised when an operation times out."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "TIMEOUT_ERROR")
        super().__init__(message, *args, **kwargs)


class RateLimitError(PepperPyError):
    """Raised when a rate limit is exceeded."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "RATE_LIMIT_ERROR")
        super().__init__(message, *args, **kwargs)


class ServiceUnavailableError(PepperPyError):
    """Raised when a service is unavailable."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: The error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        kwargs["code"] = kwargs.get("code", "SERVICE_UNAVAILABLE")
        super().__init__(message, *args, **kwargs)


# Utility functions
def get_env_var(name: str, default: Any = None) -> Any:
    """Get an environment variable.

    Args:
        name: The name of the environment variable
        default: The default value to return if the variable is not set

    Returns:
        The value of the environment variable, or the default value
    """
    return os.environ.get(name, default)


def get_project_root() -> Path:
    """Get the root directory of the project.

    Returns:
        The root directory of the project
    """
    return Path(__file__).parent.parent.parent


def get_config_dir() -> Path:
    """Get the configuration directory.

    Returns:
        The configuration directory
    """
    return get_project_root() / "config"


def get_data_dir() -> Path:
    """Get the data directory.

    Returns:
        The data directory
    """
    return get_project_root() / "data"


def get_output_dir() -> Path:
    """Get the output directory.

    Returns:
        The output directory
    """
    return get_project_root() / "output"


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure that a directory exists.

    Args:
        path: The path to the directory

    Returns:
        The path to the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logger(
    name: str,
    level: Optional[int] = None,
    format_str: Optional[str] = None,
) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name
        level: Log level (default: INFO)
        format_str: Log format string (default: standard format)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if level is None:
        level = logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        if format_str is None:
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Export all functions
__all__ = ["get_logger"]
