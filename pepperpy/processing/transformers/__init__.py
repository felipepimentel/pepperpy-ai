"""Base transformer implementations.

This module provides base classes for data transformers:
- BaseTransformer: Core transformer interface
- DataTransformer: Generic data transformer base
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger

# Type variables
T = TypeVar("T")
TransformerType = TypeVar("TransformerType", bound="BaseTransformer")


class TransformerConfig(BaseModel):
    """Base configuration for transformers.

    Attributes:
        name: Transformer name
        enabled: Whether transformer is enabled
        metadata: Additional configuration metadata
    """

    name: str = Field(description="Transformer name")
    enabled: bool = Field(default=True, description="Whether transformer is enabled")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseTransformer(Lifecycle, Generic[T]):
    """Base class for all transformers.

    All transformers must implement this interface to ensure consistent
    behavior across the framework.
    """

    def __init__(self, config: TransformerConfig | None = None) -> None:
        """Initialize transformer.

        Args:
            config: Optional transformer configuration
        """
        super().__init__()
        self.config = config or TransformerConfig(name=self.__class__.__name__)
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize transformer.

        This method should be called before using the transformer.
        """
        try:
            self._state = ComponentState.RUNNING
            logger.info(f"Transformer initialized: {self.config.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize transformer: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up transformer resources."""
        try:
            self._state = ComponentState.UNREGISTERED
            logger.info(f"Transformer cleaned up: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup transformer: {e}")
            raise

    @abstractmethod
    async def transform(self, data: T) -> T:
        """Transform data.

        Args:
            data: Data to transform

        Returns:
            Transformed data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


class DataTransformer(BaseTransformer[T]):
    """Base class for data transformers."""

    async def transform(self, data: T) -> T:
        """Transform data.

        Args:
            data: Data to transform

        Returns:
            Transformed data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


__all__ = [
    "BaseTransformer",
    "DataTransformer",
    "TransformerConfig",
]
