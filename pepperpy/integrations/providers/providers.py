"""Provider factories module.

This module provides factory implementations for adapter providers.
"""

import logging
from typing import Dict, Optional

from pepperpy.adapters.autogen import AutoGenAdapter, AutoGenConfig
from pepperpy.adapters.factories.base import BaseAdapterFactory
from pepperpy.adapters.types import (
    AdapterConfig,
    AdapterContext,
    AdapterSpec,
    AdapterType,
    AdapterValidation,
)
from pepperpy.core.errors import AdapterError

logger = logging.getLogger(__name__)


class AutoGenFactory(BaseAdapterFactory):
    """Factory for AutoGen adapters."""

    def __init__(self) -> None:
        """Initialize factory."""
        spec = AdapterSpec(
            name="autogen",
            type=AdapterType.FRAMEWORK,
            version="1.0.0",
            description="AutoGen framework adapter",
            config_class=AutoGenConfig,
            context_class=AdapterContext,
            validation=AdapterValidation(
                config_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "parameters": {"type": "object"},
                    },
                    "required": ["name"],
                }
            ),
        )
        super().__init__(adapter_type=AutoGenAdapter, spec=spec)

    async def _create_adapter(
        self,
        config: AdapterConfig,
        context: Optional[AdapterContext] = None,
    ) -> AutoGenAdapter:
        """Create AutoGen adapter instance.

        Args:
            config: Adapter configuration
            context: Optional adapter context

        Returns:
            AutoGenAdapter: Created adapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        try:
            if not isinstance(config, AutoGenConfig):
                raise AdapterError("Invalid configuration type")

            # Create adapter instance
            adapter = AutoGenAdapter(
                config=config,
                context=context or self._create_context(config),
            )

            return adapter

        except Exception as e:
            logger.error(
                f"Failed to create AutoGen adapter: {e}",
                extra={"config": config.dict()},
                exc_info=True,
            )
            raise AdapterError(f"Failed to create AutoGen adapter: {e}") from e

    async def _validate_config(self, config: AdapterConfig) -> None:
        """Validate AutoGen configuration.

        Args:
            config: Configuration to validate

        Raises:
            AdapterError: If validation fails
        """
        try:
            if not isinstance(config, AutoGenConfig):
                raise AdapterError("Invalid configuration type")

            # Validate required fields
            if not config.name:
                raise AdapterError("Missing required field: name")

            # Validate version format
            if config.version and not _is_valid_version(config.version):
                raise AdapterError("Invalid version format")

            # Validate parameters
            if config.parameters:
                _validate_parameters(config.parameters)

        except Exception as e:
            logger.error(
                f"AutoGen configuration validation failed: {e}",
                extra={"config": config.dict()},
                exc_info=True,
            )
            raise AdapterError(f"Invalid AutoGen configuration: {e}") from e


def _is_valid_version(version: str) -> bool:
    """Validate version string format.

    Args:
        version: Version string

    Returns:
        bool: True if valid
    """
    try:
        major, minor, patch = version.split(".")
        return all(part.isdigit() for part in (major, minor, patch))
    except ValueError:
        return False


def _validate_parameters(parameters: Dict) -> None:
    """Validate adapter parameters.

    Args:
        parameters: Parameters to validate

    Raises:
        AdapterError: If validation fails
    """
    # Add parameter-specific validation here
    pass
