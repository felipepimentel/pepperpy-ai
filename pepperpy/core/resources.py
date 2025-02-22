"""Core resource management.

This module provides base classes and utilities for resource management,
including initialization, cleanup, and automatic resource management.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional, TypeVar

from pepperpy.core.errors import LifecycleError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Resource(ABC):
    """Base class for all resources.

    This class defines the interface that all resources must implement.
    It provides lifecycle management and automatic cleanup capabilities.

    Attributes:
        auto_cleanup: Whether to automatically clean up expired resources
        cleanup_interval: Interval in seconds between cleanup runs
        _cleanup_task: Optional background task for automatic cleanup
        _initialized: Whether the resource has been initialized
    """

    def __init__(
        self,
        auto_cleanup: bool = True,
        cleanup_interval: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize resource.

        Args:
            auto_cleanup: Whether to automatically clean up expired resources
            cleanup_interval: Interval in seconds between cleanup runs
            **kwargs: Additional resource-specific configuration
        """
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self.config = kwargs
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the resource.

        This method must be called before using the resource.
        It will initialize any required resources and start background tasks.

        Raises:
            StateError: If already initialized
            ConfigError: If initialization fails
        """
        if self._initialized:
            return

        try:
            await self._initialize()
            self._initialized = True

            if self.auto_cleanup and self.cleanup_interval:
                self._cleanup_task = asyncio.create_task(self._run_cleanup())
        except Exception as e:
            raise LifecycleError(f"Failed to initialize resource: {e}")

    async def cleanup(self) -> None:
        """Clean up the resource.

        This method must be called when the resource is no longer needed.
        It will clean up any allocated resources and stop background tasks.

        Raises:
            StateError: If not initialized
            ConfigError: If cleanup fails
        """
        if not self._initialized:
            return

        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            await self._cleanup()
            self._initialized = False
        except Exception as e:
            raise LifecycleError(f"Failed to clean up resource: {e}")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize resource implementation.

        This method must be implemented by subclasses to perform
        resource-specific initialization.

        Raises:
            ConfigError: If initialization fails
        """
        raise NotImplementedError

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up resource implementation.

        This method must be implemented by subclasses to perform
        resource-specific cleanup.

        Raises:
            ConfigError: If cleanup fails
        """
        raise NotImplementedError

    async def _run_cleanup(self) -> None:
        """Run automatic cleanup task.

        This method runs in the background to periodically clean up
        expired resources.
        """
        if not self.cleanup_interval:
            return

        while True:
            try:
                await asyncio.sleep(float(self.cleanup_interval))
                await self._cleanup()
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")

    @abstractmethod
    async def process(self, input: str) -> str:
        """Process input and generate response.

        This method must be implemented by subclasses to process input
        and generate appropriate responses.

        Args:
            input: Input text to process

        Returns:
            Generated response

        Raises:
            NotImplementedError: Must be implemented by subclasses
            ProcessingError: If processing fails
        """
        raise NotImplementedError


@asynccontextmanager
async def resource_session(resource: Resource) -> AsyncGenerator[Resource, None]:
    """Context manager for automatic resource lifecycle management.

    Args:
        resource: Resource to manage

    Yields:
        Initialized resource

    Raises:
        LifecycleError: If resource lifecycle operations fail
    """
    try:
        await resource.initialize()
        yield resource
    finally:
        await resource.cleanup()
