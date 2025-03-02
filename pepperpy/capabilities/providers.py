"""Provider capabilities for the Pepperpy framework.

This module defines the base provider capabilities and interfaces used
throughout the framework. It includes:
- Provider capability interface
- Provider configuration
- Provider lifecycle management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.base import Capability
from pepperpy.core.common.messages import ProviderMessage, ProviderResponse

# Type variables
T = TypeVar("T")
ProviderType = TypeVar("ProviderType", bound="ProviderCapability")


class ProviderConfig(BaseModel):
    """Provider configuration model.

    Attributes:
        id: Unique provider identifier
        type: Provider type identifier
        config: Provider-specific configuration
    """

    id: UUID = Field(default_factory=uuid4)
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)


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
        pass

    @abstractmethod
    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        pass

    @abstractmethod
    async def get_info(self) -> Dict[str, Any]:
        """Get provider information.

        Returns:
            Dictionary containing provider information
        """
        pass
