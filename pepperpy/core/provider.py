"""Provider interface.

This module defines the base provider interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Provider(ABC):
    """Base provider interface."""

    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize provider.

        Args:
            config: Optional provider configuration
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown provider."""
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name
        """
        raise NotImplementedError

    @abstractmethod
    def get_version(self) -> str:
        """Get provider version.

        Returns:
            Provider version
        """
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str:
        """Get provider description.

        Returns:
            Provider description
        """
        raise NotImplementedError

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Provider capabilities
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get provider status.

        Returns:
            Provider status
        """
        raise NotImplementedError

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics.

        Returns:
            Provider metrics
        """
        raise NotImplementedError

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration.

        Returns:
            Provider configuration
        """
        raise NotImplementedError

    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update provider configuration.

        Args:
            config: New configuration

        Returns:
            Updated configuration
        """
        raise NotImplementedError
