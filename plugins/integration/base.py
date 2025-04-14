"""Base module for integration plugins.

This module provides the core interfaces and factories for integration plugins.
"""

import importlib
import logging
from typing import Any, TypeVar, cast

from pepperpy.core.base import PepperpyError
from pepperpy.plugin import ProviderPlugin

logger = logging.getLogger(__name__)


class IntegrationError(PepperpyError):
    """Base exception for all integration-related errors."""


T = TypeVar("T", bound="IntegrationProvider")


class IntegrationProvider(ProviderPlugin):
    """Base class for all integration providers."""

    async def initialize(self) -> None:
        """Initialize the integration provider."""
        raise NotImplementedError("Must be implemented by subclass")

    async def cleanup(self) -> None:
        """Clean up resources."""
        raise NotImplementedError("Must be implemented by subclass")


def create_integration_provider(
    provider_type: str, provider_name: str, **config: Any
) -> IntegrationProvider:
    """Create an integration provider instance.

    Args:
        provider_type: Type of integration provider (e.g., "weather")
        provider_name: Name of the provider implementation (e.g., "openweather")
        **config: Provider configuration parameters

    Returns:
        Initialized integration provider

    Raises:
        IntegrationError: If the provider type or implementation is not found
    """
    try:
        # Dynamically import the provider module
        module_path = f"plugins.integration.{provider_type}.{provider_name}.provider"
        module = importlib.import_module(module_path)

        # Find the provider class (naming convention: XxxProvider)
        provider_class_name = None
        for name in dir(module):
            if name.endswith("Provider") and not name.startswith("_"):
                provider_class_name = name
                break

        if not provider_class_name:
            raise IntegrationError(f"Provider class not found in {module_path}")

        # Create provider instance
        provider_class = getattr(module, provider_class_name)
        provider = provider_class(**config)

        return cast(IntegrationProvider, provider)
    except ImportError as e:
        raise IntegrationError(f"Integration provider not found: {e}") from e
    except Exception as e:
        raise IntegrationError(f"Error creating integration provider: {e}") from e
