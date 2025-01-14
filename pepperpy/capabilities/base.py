"""Base capability module."""

from typing import Generic, TypeVar

from pepperpy.types import BaseConfig

T = TypeVar("T", bound=BaseConfig)


class BaseCapability(Generic[T]):
    """Base capability class."""

    def __init__(self, config: T) -> None:
        """Initialize capability.

        Args:
            config: Capability configuration.
        """
        self._config = config
        self._initialized = False

    @property
    def config(self) -> T:
        """Get capability configuration.

        Returns:
            T: Capability configuration.
        """
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Return whether the capability is initialized.

        Returns:
            bool: Whether the capability is initialized.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize capability."""
        if not self.is_initialized:
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up capability."""
        self._initialized = False
