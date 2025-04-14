"""Base service interface for PepperPy API.

This module provides the base interfaces and abstract classes for all API services.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any


class BaseService(ABC):
    """Base class for all API services.

    All services in the API should inherit from this base class to ensure
    consistent initialization, cleanup, and status reporting.
    """

    def __init__(self) -> None:
        """Initialize the service."""
        self._initialized = False
        self._start_time = time.time()
        self.logger = logging.getLogger(
            f"api.services.{self.__class__.__name__.lower()}"
        )
        self.logger.info(f"{self.__class__.__name__} created")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources.

        This method should be implemented by service subclasses to initialize
        any resources needed by the service.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources.

        This method should be implemented by service subclasses to clean up
        any resources used by the service.
        """
        pass

    async def get_status(self) -> dict[str, Any]:
        """Get the current status of the service.

        Returns:
            A dictionary containing service metrics and status
        """
        return {
            "status": "running" if self._initialized else "initializing",
            "uptime_seconds": time.time() - self._start_time,
            "service_type": self.__class__.__name__,
        }

    async def reset(self) -> None:
        """Reset the service state.

        By default, this method cleans up resources and reinitializes the service.
        Subclasses can override this method to provide custom reset behavior.
        """
        self.logger.info(f"Resetting {self.__class__.__name__}")

        # Clean up resources
        if self._initialized:
            await self.cleanup()

        # Reinitialize
        await self.initialize()

        self.logger.info(f"{self.__class__.__name__} reset completed")
