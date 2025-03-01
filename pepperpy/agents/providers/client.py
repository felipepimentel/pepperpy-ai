from collections.abc import AsyncGenerator
from typing import Any, Dict, Union

from pepperpy.providers.agent.base import BaseProvider
from pepperpy.providers.agent.domain import ProviderConfig, ProviderError
from pepperpy.providers.agent.types import ProviderMessage, ProviderResponse


# Alias for backward compatibility
class ProviderConfigurationError(ProviderError):
    """Configuration error for providers."""

    pass


class ClientProvider(BaseProvider):
    """Client provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize client provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self._initialized:
            return

        try:
            # Initialize client with config
            self._client = await self._create_client(self.config)
            self._initialized = True
        except Exception as e:
            raise ProviderError(f"Failed to initialize client provider: {e}")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            await self._client.close()
        self._initialized = False

    async def process_message(
        self,
        message: ProviderMessage,
    ) -> Union[ProviderResponse, AsyncGenerator[ProviderResponse, None]]:
        """Process a provider message.

        Args:
            message: Provider message to process

        Returns:
            Provider response or async generator of responses

        Raises:
            ProviderError: If message processing fails
            ProviderConfigurationError: If provider is not initialized
        """
        if not self._initialized:
            await self.initialize()

        if not self._client:
            raise ProviderConfigurationError("Client not initialized")

        try:
            response = await self._client.process_message(message)
            if isinstance(response, AsyncGenerator):
                return response
            return ProviderResponse(
                provider_id=self.id,
                provider_type=self.type,
                content=str(response.get("content", "")),
                metadata=response.get("metadata", {}),
            )
        except Exception as e:
            raise ProviderError(f"Failed to process message: {e}")

    async def _create_client(self, config: Dict[str, Any]) -> Any:
        """Create client instance.

        Args:
            config: Client configuration

        Returns:
            Client instance

        Raises:
            ProviderError: If client creation fails
            ProviderConfigurationError: If configuration is invalid
        """
        # TODO: Implement client creation
        raise NotImplementedError("Client creation not implemented")
