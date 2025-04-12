"""
PepperPy Plugin Compatibility Module.

This module provides backward compatibility for plugins that import from pepperpy.plugin.plugin.
"""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ProviderPlugin(Protocol):
    """Protocol for provider plugins.

    This is a standalone definition that doesn't depend on other framework components,
    ensuring it can be imported safely regardless of the import chain state.

    All PepperPy provider plugins should conform to this protocol to ensure
    consistent behavior and resource management.
    """

    @property
    def initialized(self) -> bool:
        """Check if the provider is initialized.

        Returns:
            Boolean indicating if the provider has been initialized
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider to ensure
        all necessary resources are properly initialized.
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed
        to ensure all resources are properly released.
        """
        ...

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if the key is not found

        Returns:
            Configuration value or default
        """
        ...

    def has_config(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Configuration key

        Returns:
            True if the key exists, False otherwise
        """
        ...

    def update_config(self, **kwargs: Any) -> None:
        """Update the configuration.

        Args:
            **kwargs: Configuration values to update
        """
        ...

    async def __aenter__(self) -> "ProviderPlugin":
        """Enter the async context.

        Returns:
            Self
        """
        await self.initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Exit the async context.

        This method ensures resources are cleaned up when exiting
        the context manager.
        """
        await self.cleanup()


__all__ = ["ProviderPlugin"]
