"""Public Interface for Cloud Providers

This module provides a stable public interface for cloud provider functionality.
It exposes the core cloud provider abstractions and implementations that are
considered part of the public API.

Core Components:
    CloudProvider: Base class for cloud providers
    CloudProviderConfig: Configuration for cloud providers
    CloudService: Base class for cloud services
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CloudProviderConfig:
    """Base configuration for cloud providers.

    Attributes:
        provider_name: Name of the cloud provider
        region: Cloud region
        credentials: Optional provider credentials

    """

    provider_name: str
    region: str
    credentials: Dict[str, Any] = field(default_factory=dict)


class CloudProvider(ABC):
    """Base class for cloud providers.

    This class defines the interface for cloud providers,
    which are responsible for interacting with cloud services.
    """

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
            True if configuration is valid

        Raises:
            Exception: If validation fails

        """

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized.

        Returns:
            True if initialized

        """
        return self._initialized


class CloudService(ABC):
    """Base class for cloud services.

    This class defines the interface for cloud services,
    which provide specific functionality within a cloud provider.
    """

    def __init__(self, provider: CloudProvider, name: str):
        """Initialize cloud service.

        Args:
            provider: Cloud provider
            name: Service name

        """
        self.provider = provider
        self.name = name

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources.

        Raises:
            Exception: If initialization fails

        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources.

        Raises:
            Exception: If cleanup fails

        """


# Export public classes
__all__ = [
    "CloudProvider",
    "CloudProviderConfig",
    "CloudService",
]
