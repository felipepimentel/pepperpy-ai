"""PepperPy Applications Module.

This module provides high-level applications built on the PepperPy framework.
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.errors import PepperPyError
from pepperpy.core.logging import get_logger

# Setup logging
logger = get_logger(__name__)


class AppError(PepperPyError):
    """Error raised when an application operation fails."""

    pass


class Application:
    """Base class for PepperPy applications."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize an application.

        Args:
            name: The name of the application
            config: Optional configuration for the application
        """
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"{__name__}.{name}")

    async def initialize(self) -> None:
        """Initialize the application.

        This method should be overridden by subclasses to perform
        any necessary initialization.
        """
        self.logger.info(f"Initializing application: {self.name}")

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the application.

        This method should be overridden by subclasses to implement
        the application's functionality.

        Args:
            *args: Positional arguments for the application
            **kwargs: Keyword arguments for the application

        Returns:
            The result of running the application
        """
        raise NotImplementedError("Application must implement run method")

    async def shutdown(self) -> None:
        """Shutdown the application.

        This method should be overridden by subclasses to perform
        any necessary cleanup.
        """
        self.logger.info(f"Shutting down application: {self.name}")


class ApplicationRegistry:
    """Registry for applications."""

    def __init__(self):
        """Initialize the registry."""
        self._applications: Dict[str, Application] = {}

    def register(self, app: Application) -> None:
        """Register an application.

        Args:
            app: The application to register

        Raises:
            AppError: If an application with the same name is already registered
        """
        if app.name in self._applications:
            raise AppError(f"Application {app.name} already registered")
        self._applications[app.name] = app

    def get(self, name: str) -> Optional[Application]:
        """Get an application by name.

        Args:
            name: The name of the application

        Returns:
            The application, or None if not found
        """
        return self._applications.get(name)

    def list(self) -> List[str]:
        """List all registered application names.

        Returns:
            A list of all registered application names
        """
        return list(self._applications.keys())

    def unregister(self, name: str) -> None:
        """Unregister an application.

        Args:
            name: The name of the application to unregister
        """
        if name in self._applications:
            del self._applications[name]


# Global registry instance
_registry = ApplicationRegistry()


def register_app(app: Application) -> None:
    """Register an application.

    Args:
        app: The application to register

    Raises:
        AppError: If an application with the same name is already registered
    """
    _registry.register(app)


def get_app(name: str) -> Optional[Application]:
    """Get an application by name.

    Args:
        name: The name of the application

    Returns:
        The application, or None if not found
    """
    return _registry.get(name)


def list_apps() -> List[str]:
    """List all registered application names.

    Returns:
        A list of all registered application names
    """
    return _registry.list()


def unregister_app(name: str) -> None:
    """Unregister an application.

    Args:
        name: The name of the application to unregister
    """
    _registry.unregister(name)


__all__ = [
    "AppError",
    "Application",
    "ApplicationRegistry",
    "register_app",
    "get_app",
    "list_apps",
    "unregister_app",
]
