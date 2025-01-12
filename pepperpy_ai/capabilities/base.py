"""Base capability module."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..config.capability import CapabilityConfig
from ..providers.base import BaseProvider

T = TypeVar("T", bound=BaseProvider)


class BaseCapability(ABC, Generic[T]):
    """Base class for capabilities.

    This class provides the foundation for implementing different capabilities.
    Each capability can implement its own initialization, cleanup, and provider
    management methods to support different use cases and requirements.
    """

    def __init__(self, config: CapabilityConfig, provider: type[T]) -> None:
        """Initialize capability.

        Args:
            config: Capability configuration.
            provider: Provider class to use.
        """
        self.config = config
        self.provider = provider
        self._initialized = False
        self._provider_instance: T | None = None

    @property
    def is_initialized(self) -> bool:
        """Check if capability is initialized."""
        return self._initialized

    def _ensure_initialized(self) -> None:
        """Ensure capability is initialized.

        Raises:
            RuntimeError: If capability is not initialized.
        """
        if not self.is_initialized:
            raise RuntimeError("Capability not initialized")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize capability resources."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up capability resources."""
        pass
