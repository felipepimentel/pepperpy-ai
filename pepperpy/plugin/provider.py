"""
PepperPy Provider Implementation.

This module provides base implementation for plugin providers.
"""

from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PepperpyPlugin, ResourceMixin, ResourceType


class BasePluginProvider(ResourceMixin, PepperpyPlugin):
    """Base class for plugin providers.

    This class provides common functionality for all plugin providers,
    including initialization, cleanup, and resource management.
    """

    def __init__(self, **kwargs: Any):
        """Initialize the provider.

        Args:
            **kwargs: Provider configuration
        """
        self.config: dict[str, Any] = kwargs
        self.initialized: bool = False
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    async def initialize(self) -> None:
        """Initialize the provider.

        Subclasses should override this method to perform actual initialization.
        """
        if self.initialized:
            return

        self.initialized = True
        self.logger.debug("Provider initialized")

    async def cleanup(self) -> None:
        """Clean up resources used by the provider.

        Subclasses should override this method to perform actual cleanup.
        """
        if not self.initialized:
            return

        try:
            # Clean up resources using the instance method inherited from ResourceMixin
            await self.cleanup_resources()
        except Exception as e:
            self.logger.error(f"Error cleaning up resources: {e}")

        self.initialized = False
        self.logger.debug("Provider cleaned up")

    async def __aenter__(self) -> "BasePluginProvider":
        """Enter the async context.

        Returns:
            Self
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        await self.cleanup()

    async def get_resources(self) -> list[ResourceType]:
        """Get resources provided by this plugin.

        Returns:
            List of resource types
        """
        return []

    async def can_handle_type(self, content_type: str) -> bool:
        """Check if the plugin can handle the given content type.

        Args:
            content_type: MIME type or extension

        Returns:
            True if the plugin can handle the content type, False otherwise
        """
        return False

    async def detect_type(
        self, content: str | bytes, filename: str | None = None
    ) -> str | None:
        """Detect the type of the given content.

        Args:
            content: Content to analyze
            filename: Optional filename with extension

        Returns:
            Detected content type or None if not detected
        """
        return None

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if the key is not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def has_config(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Configuration key

        Returns:
            True if the key exists, False otherwise
        """
        return key in self.config

    def update_config(self, **kwargs: Any) -> None:
        """Update the configuration.

        Args:
            **kwargs: Configuration values to update
        """
        self.config.update(kwargs)
