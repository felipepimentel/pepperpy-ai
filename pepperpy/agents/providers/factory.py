"""Factory for creating providers in the Pepperpy framework.

This module provides the factory implementation for creating different types
of providers based on configuration.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pepperpy.agents.providers.base import BaseProvider
from pepperpy.agents.providers.domain import (
    ProviderConfig,
    ProviderMetadata,
)
from pepperpy.common.base import BaseComponent
from pepperpy.common.errors import ConfigurationError
from pepperpy.common.logging import get_logger
from pepperpy.common.types import ComponentState

logger = get_logger(__name__)


class ProviderFactory(BaseComponent):
    """Factory for creating providers.

    This factory is responsible for creating provider instances based on
    configuration and managing their lifecycle.

    Attributes:
        id: Unique identifier for the factory
        metadata: Factory metadata
        _provider_types: Mapping of provider type names to provider classes

    """

    def __init__(
        self,
        id: UUID,
        metadata: ProviderMetadata | None = None,
    ) -> None:
        """Initialize the provider factory.

        Args:
            id: Unique identifier for the factory
            metadata: Optional factory metadata

        """
        super().__init__(id, metadata)
        self._provider_types: dict[str, type[BaseProvider]] = {}
        self._logger = logger.getChild(self.__class__.__name__)
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize the factory.

        This method is called during factory startup to perform any necessary
        initialization.

        Raises:
            ConfigurationError: If initialization fails

        """
        try:
            self._state = ComponentState.INITIALIZED
            # Initialize provider type registry
            self._provider_types.clear()
            self._logger.info("Provider factory initialized")
            self._state = ComponentState.RUNNING
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ConfigurationError(f"Failed to initialize factory: {e}") from e

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        try:
            self._provider_types.clear()
            self._logger.info("Provider factory cleaned up")
            self._state = ComponentState.UNREGISTERED
        except Exception as e:
            self._state = ComponentState.ERROR
            self._logger.error(f"Error during factory cleanup: {e}")
            raise

    def register_provider_type(
        self, name: str, provider_class: type[BaseProvider]
    ) -> None:
        """Register a provider type.

        Args:
            name: Name of the provider type
            provider_class: Provider class to register

        Raises:
            ConfigurationError: If provider type is invalid

        """
        if not name:
            raise ConfigurationError("Provider type name is required")
        if not issubclass(provider_class, BaseProvider):
            raise ConfigurationError(
                f"Invalid provider class: {provider_class.__name__}"
            )

        self._provider_types[name] = provider_class
        self._logger.info("Registered provider type", extra={"type": name})

    async def create_provider(
        self,
        provider_type: str,
        config: ProviderConfig | None = None,
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            provider_type: Type of provider to create
            config: Optional provider configuration

        Returns:
            Created provider instance

        Raises:
            ConfigurationError: If provider type is not supported

        """
        if not provider_type:
            raise ConfigurationError("Provider type not specified")

        provider_class = self._provider_types.get(provider_type)
        if not provider_class:
            raise ConfigurationError(f"Unsupported provider type: {provider_type}")

        try:
            # Create provider metadata
            now = datetime.utcnow()
            metadata = ProviderMetadata(
                created_at=now,
                updated_at=now,
                version="1.0.0",
                tags=[provider_type],
                properties={},
                provider_type=provider_type,
                capabilities=[],
                settings=config.settings if config else {},
                statistics={},
            )

            # Create provider instance
            provider = provider_class(
                id=uuid4(),
                metadata=metadata,
                config=config,
            )

            # Initialize provider
            await provider.initialize()

            self._logger.info(
                "Created provider",
                extra={
                    "type": provider_type,
                    "id": str(provider.id),
                },
            )
            return provider

        except Exception as e:
            self._logger.error(
                "Failed to create provider",
                extra={
                    "type": provider_type,
                    "error": str(e),
                },
            )
            raise ConfigurationError(f"Failed to create provider: {e}") from e

    async def execute(self, **kwargs: Any) -> Any:
        """Execute factory functionality.

        This method implements the BaseComponent interface.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution results

        """
        provider_type = kwargs.get("provider_type")
        config = kwargs.get("config")
        if not provider_type:
            raise ConfigurationError("Provider type is required")
        return await self.create_provider(provider_type, config)

    def validate(self) -> None:
        """Validate factory state.

        Raises:
            ConfigurationError: If factory state is invalid

        """
        super().validate()
        if not isinstance(self._provider_types, dict):
            raise ConfigurationError("Provider types must be a dictionary")
