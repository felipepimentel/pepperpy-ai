"""Base service provider for agents.

This module provides the base implementation for service-based agent providers.
"""

from typing import Optional

from pepperpy.core.metrics import MetricsManager
from pepperpy.core.monitoring import logger
from pepperpy.core.providers.base import BaseProvider, ProviderConfig


class ServiceProvider(BaseProvider):
    """Base class for service-based agent providers.

    This class provides common functionality for providers that interact
    with external services.
    """

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        """Initialize service provider.

        Args:
            config: Optional provider configuration
        """
        super().__init__(config=config or ProviderConfig(type="service"))
        self.config = config or ProviderConfig(type="service")
        self._metrics = MetricsManager.get_instance()
        logger.debug("Initialized service provider with config: %s", self.config)

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        """
        try:
            # Initialize service connection
            await self._initialize_service()
            self._metrics.increment("provider.service.successful_initializations")
            logger.info("Service provider initialized successfully")
        except Exception as e:
            self._metrics.increment("provider.service.initialization_errors")
            logger.error("Failed to initialize service provider: %s", e)
            raise

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        """
        try:
            # Clean up service connection
            await self._cleanup_service()
            self._metrics.increment("provider.service.successful_cleanups")
            logger.info("Service provider cleaned up successfully")
        except Exception as e:
            self._metrics.increment("provider.service.cleanup_errors")
            logger.error("Failed to clean up service provider: %s", e)
            raise

    async def _initialize_service(self) -> None:
        """Initialize service connection.

        This method should be implemented by subclasses to handle
        service-specific initialization.
        """
        pass

    async def _cleanup_service(self) -> None:
        """Clean up service connection.

        This method should be implemented by subclasses to handle
        service-specific cleanup.
        """
        pass
