"""Base provider capability interface.

This module defines the base provider capability interface that all providers
must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from pepperpy.capabilities.providers.base.types import ProviderConfig
from pepperpy.core.base import Capability
from pepperpy.core.common.messages import ProviderMessage, ProviderResponse


class ProviderCapability(Capability, ABC):
    """Base provider capability interface.

    All providers must implement this interface to ensure consistent
    behavior across the framework.
    """

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider capability.

        Args:
            config: Provider configuration

        """
        super().__init__()
        self.id = config.id
        self.type = config.type
        self.config = config.config

    @abstractmethod
    async def process_message(
        self,
        message: ProviderMessage,
    ) -> ProviderResponse:
        """Process a provider message.

        Args:
            message: Provider message to process

        Returns:
            Provider response

        Raises:
            ProviderError: If message processing fails
            ConfigurationError: If provider is not initialized

        """

    @abstractmethod
    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails

        """

    @abstractmethod
    async def get_info(self) -> Dict[str, Any]:
        """Get provider information.

        Returns:
            Dictionary containing provider information

        """
