"""Base adapter factory module.

This module provides base implementations for adapter factories.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from pepperpy.adapters.base import BaseAdapter
from pepperpy.adapters.types import (
    AdapterConfig,
    AdapterContext,
    AdapterMetadata,
    AdapterSpec,
    AdapterState,
)
from pepperpy.core.errors import AdapterError

logger = logging.getLogger(__name__)


class BaseAdapterFactory(ABC):
    """Base adapter factory implementation.

    This class provides a base implementation for adapter factories with
    improved validation and configuration handling.
    """

    def __init__(
        self,
        adapter_type: Type[BaseAdapter],
        spec: AdapterSpec,
    ) -> None:
        """Initialize factory.

        Args:
            adapter_type: Adapter class type
            spec: Adapter specification
        """
        self._adapter_type = adapter_type
        self._spec = spec
        self._config_cache: Dict[str, AdapterConfig] = {}

    @property
    def adapter_type(self) -> Type[BaseAdapter]:
        """Get adapter type."""
        return self._adapter_type

    @property
    def spec(self) -> AdapterSpec:
        """Get adapter specification."""
        return self._spec

    async def create(
        self,
        config: AdapterConfig,
        context: Optional[AdapterContext] = None,
        metadata: Optional[AdapterMetadata] = None,
    ) -> BaseAdapter:
        """Create adapter instance.

        Args:
            config: Adapter configuration
            context: Optional adapter context
            metadata: Optional adapter metadata

        Returns:
            BaseAdapter: Created adapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        try:
            # Validate configuration
            await self.validate_config(config)

            # Create adapter instance
            adapter = await self._create_adapter(config, context)

            # Set metadata if provided
            if metadata:
                adapter.metadata = metadata

            logger.info(
                f"Created adapter: {adapter.name}",
                extra={
                    "adapter": adapter.name,
                    "type": str(adapter.type),
                    "version": adapter.version,
                },
            )

            return adapter

        except Exception as e:
            logger.error(
                f"Failed to create adapter: {e}",
                extra={"config": config.dict()},
                exc_info=True,
            )
            raise AdapterError(f"Failed to create adapter: {e}") from e

    async def validate_config(self, config: AdapterConfig) -> None:
        """Validate adapter configuration.

        Args:
            config: Adapter configuration to validate

        Raises:
            AdapterError: If configuration validation fails
        """
        try:
            # Validate against specification
            if self._spec.validation and self._spec.validation.config_schema:
                self._spec.validation.config_schema.validate(config)

            # Custom validation
            await self._validate_config(config)

        except Exception as e:
            logger.error(
                f"Configuration validation failed: {e}",
                extra={"config": config.dict()},
                exc_info=True,
            )
            raise AdapterError(f"Invalid configuration: {e}") from e

    @abstractmethod
    async def _create_adapter(
        self,
        config: AdapterConfig,
        context: Optional[AdapterContext] = None,
    ) -> BaseAdapter:
        """Create adapter instance.

        Args:
            config: Adapter configuration
            context: Optional adapter context

        Returns:
            BaseAdapter: Created adapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        raise NotImplementedError

    @abstractmethod
    async def _validate_config(self, config: AdapterConfig) -> None:
        """Validate adapter configuration.

        Args:
            config: Adapter configuration to validate

        Raises:
            AdapterError: If configuration validation fails
        """
        raise NotImplementedError

    def _create_context(self, config: AdapterConfig) -> AdapterContext:
        """Create adapter context.

        Args:
            config: Adapter configuration

        Returns:
            AdapterContext: Created context
        """
        return AdapterContext(
            adapter_id=config.name,
            config=config,
            state=AdapterState.CREATED,
        )
