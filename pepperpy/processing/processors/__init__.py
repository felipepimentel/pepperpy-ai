"""Base processor implementations.

This module provides base classes for processors:
- BaseProcessor: Core processor interface
- ContentProcessor: Content processing base
- AudioProcessor: Audio processing base
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger

# Type variables
T = TypeVar("T")
ProcessorType = TypeVar("ProcessorType", bound="BaseProcessor")


class ProcessorConfig(BaseModel):
    """Base configuration for processors.

    Attributes:
        name: Processor name
        enabled: Whether processor is enabled
        metadata: Additional configuration metadata
    """

    name: str = Field(description="Processor name")
    enabled: bool = Field(default=True, description="Whether processor is enabled")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseProcessor(Lifecycle, Generic[T]):
    """Base class for all processors.

    All processors must implement this interface to ensure consistent
    behavior across the framework.
    """

    def __init__(self, config: Optional[ProcessorConfig] = None) -> None:
        """Initialize processor.

        Args:
            config: Optional processor configuration
        """
        super().__init__()
        self.config = config or ProcessorConfig(name=self.__class__.__name__)
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize processor.

        This method should be called before using the processor.
        """
        try:
            self._state = ComponentState.RUNNING
            logger.info(f"Processor initialized: {self.config.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize processor: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up processor resources."""
        try:
            self._state = ComponentState.UNREGISTERED
            logger.info(f"Processor cleaned up: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup processor: {e}")
            raise

    @abstractmethod
    async def process(self, data: T, **kwargs: Any) -> T:
        """Process data.

        Args:
            data: Data to process
            **kwargs: Additional processing parameters

        Returns:
            Processed data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


class ContentProcessor(BaseProcessor[T]):
    """Base class for content processors."""

    async def process(self, data: T, **kwargs: Any) -> T:
        """Process content data.

        Args:
            data: Content data to process
            **kwargs: Additional processing parameters

        Returns:
            Processed content data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


class AudioProcessor(BaseProcessor[T]):
    """Base class for audio processors."""

    async def process(self, data: T, **kwargs: Any) -> T:
        """Process audio data.

        Args:
            data: Audio data to process
            **kwargs: Additional processing parameters

        Returns:
            Processed audio data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


__all__ = [
    "ProcessorConfig",
    "BaseProcessor",
    "ContentProcessor",
    "AudioProcessor",
]
