"""Core functionality for PepperPy applications.

This module defines the base classes and core functionality for all PepperPy applications,
providing common features like configuration, logging, and state management.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.logging import get_logger


class BaseApp:
    """Base class for all PepperPy applications.

    This class provides common functionality for all PepperPy applications,
    such as configuration, logging, and state management.

    Attributes:
        name: Name of the application
        config: Application configuration
        logger: Application logger
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the application.

        Args:
            name: Name of the application
            description: Description of the application
            config: Initial application configuration
        """
        self.name = name
        self.description = description or f"Application {name}"
        self.config = config or {}
        self.logger = get_logger(f"pepperpy.apps.{name}")
        self.output_path = None
        self._initialized = False

        # Load configuration from environment variables
        self._load_env_config()

        self.logger.info(f"Application {name} initialized")

    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        env_prefix = f"PEPPERPY_{self.name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix) :].lower()
                self.config[config_key] = value
                self.logger.debug(f"Loaded environment configuration: {config_key}")

    def configure(self, **kwargs: Any) -> "BaseApp":
        """Configure the application.

        Args:
            **kwargs: Configuration parameters

        Returns:
            The application itself for method chaining
        """
        self.config.update(kwargs)
        self.logger.debug(f"Configuration updated: {kwargs}")
        return self

    def set_output_path(self, path: Union[str, Path]) -> "BaseApp":
        """Set the output path for the application.

        Args:
            path: Output path

        Returns:
            The application itself for method chaining
        """
        self.output_path = Path(path)
        # Create parent directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Output path set: {self.output_path}")
        return self

    async def initialize(self) -> None:
        """Initialize the application.

        This method should be called before using the application.
        Can be overridden by subclasses to perform specific initialization.
        """
        if self._initialized:
            return

        self.logger.info(f"Initializing application {self.name}")
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up application resources.

        This method should be called when the application is no longer needed.
        Can be overridden by subclasses to perform specific cleanup.
        """
        self.logger.info(f"Cleaning up resources for application {self.name}")

    def __repr__(self) -> str:
        """Return a string representation of the application."""
        return f"{self.__class__.__name__}(name='{self.name}')"


# Common result types and interfaces for all application types
class AppResult:
    """Base class for application results.

    This class provides common functionality for all application results.
    """

    def __init__(
        self, data: Any = None, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize the result.

        Args:
            data: Result data
            metadata: Result metadata
        """
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = os.environ.get("PEPPERPY_TIMESTAMP", "")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dictionary representation of the result
        """
        return {
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        """Return a string representation of the result."""
        return f"{self.__class__.__name__}(data={self.data!r})"
