"""Base cloud provider module.

This module defines the base classes and interfaces for cloud providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class CloudProviderConfig(BaseModel):
    """Base configuration for cloud providers."""

    provider_name: str
    region: str
    credentials: Optional[Dict[str, Any]] = None


class CloudProvider(ABC):
    """Base class for cloud providers."""

    def __init__(self, config: CloudProviderConfig):
        """Initialize cloud provider.

        Args:
            config: Provider configuration

        """
        self.config = config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider resources.

        Raises:
            Exception: If initialization fails

        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.

        Raises:
            Exception: If cleanup fails

        """

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate provider configuration.

        Returns:
            bool: True if configuration is valid

        Raises:
            Exception: If validation fails

        """

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized.

        Returns:
            bool: True if initialized

        """
        return self._initialized
