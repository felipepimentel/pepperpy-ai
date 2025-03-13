"""Base manager functionality for PepperPy.

This module provides the base functionality for managers in PepperPy.
Managers are responsible for coordinating components and providers,
such as LLM models, storage backends, or external APIs.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pepperpy.core.base_registry import Registry
from pepperpy.errors.core import PepperPyError
from pepperpy.providers.base import BaseProvider
from pepperpy.types import Identifiable
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for provider types
P = TypeVar("P", bound=BaseProvider)


class ManagerError(PepperPyError):
    """Error raised for manager-related issues."""

    pass


class BaseManager(Identifiable, Generic[P]):
    """Base class for all managers in the framework.

    A manager is responsible for coordinating components and providers.
    It typically manages a registry of providers and provides a unified
    interface for working with those providers.

    Args:
        P: The type of provider that this manager manages
    """

    def __init__(
        self,
        manager_name: str,
        manager_type: str,
        provider_registry: Optional[Registry[Type[P]]] = None,
    ):
        """Initialize the manager.

        Args:
            manager_name: The name of this manager instance
            manager_type: The type of manager (e.g., 'llm', 'rag', 'security')
            provider_registry: Optional registry for provider types
        """
        self._manager_name = manager_name
        self._manager_type = manager_type
        self._provider_registry = provider_registry or Registry(
            registry_name=f"{manager_name}_provider_registry",
            registry_type="provider",
        )
        self._default_provider_type: Optional[str] = None
        self._providers: Dict[str, P] = {}

    @property
    def id(self) -> str:
        """Get the ID of this manager.

        Returns:
            Manager ID
        """
        return f"{self._manager_type}:{self._manager_name}"

    @property
    def manager_type(self) -> str:
        """Get the manager type.

        Returns:
            Manager type
        """
        return self._manager_type

    @property
    def provider_registry(self) -> Registry[Type[P]]:
        """Get the provider registry.

        Returns:
            Provider registry
        """
        return self._provider_registry

    def register_provider(self, provider_type: str, provider_class: Type[P]) -> None:
        """Register a provider type.

        Args:
            provider_type: The type identifier
            provider_class: The provider class to register

        Raises:
            ManagerError: If registration fails
        """
        try:
            self._provider_registry.register(provider_type, provider_class)
        except Exception as e:
            raise ManagerError(f"Failed to register provider {provider_type}: {e}")

    def unregister_provider(self, provider_type: str) -> None:
        """Unregister a provider type.

        Args:
            provider_type: The type identifier to unregister

        Raises:
            ManagerError: If unregistration fails
        """
        try:
            self._provider_registry.unregister(provider_type)
        except Exception as e:
            raise ManagerError(f"Failed to unregister provider {provider_type}: {e}")

    def set_default_provider(self, provider_type: str) -> None:
        """Set the default provider type.

        Args:
            provider_type: The type identifier to set as default

        Raises:
            ManagerError: If provider type is not registered
        """
        if provider_type not in self._provider_registry._registry:
            raise ManagerError(f"Provider type {provider_type} not registered")
        self._default_provider_type = provider_type

    def get_default_provider_type(self) -> Optional[str]:
        """Get the default provider type.

        Returns:
            Default provider type if set, None otherwise
        """
        return self._default_provider_type

    async def get_provider(
        self,
        provider_type: Optional[str] = None,
        **kwargs: Any,
    ) -> P:
        """Get a provider instance.

        Args:
            provider_type: Optional provider type to use
            **kwargs: Additional arguments for provider initialization

        Returns:
            Provider instance

        Raises:
            ManagerError: If provider cannot be created
        """
        try:
            # Use default provider type if none specified
            if provider_type is None:
                if self._default_provider_type is None:
                    raise ManagerError("No default provider type set")
                provider_type = self._default_provider_type

            # Get provider class
            provider_class = self._provider_registry.get(provider_type)
            if not provider_class:
                raise ManagerError(f"Provider type {provider_type} not found")

            # Create provider instance if not cached
            if provider_type not in self._providers:
                self._providers[provider_type] = provider_class(**kwargs)

            return self._providers[provider_type]

        except Exception as e:
            raise ManagerError(f"Failed to get provider {provider_type}: {e}")

    def list_provider_types(self) -> List[str]:
        """List registered provider types.

        Returns:
            List of registered provider types
        """
        return list(self._provider_registry._registry.keys())

    async def close(self) -> None:
        """Close all providers.

        This method should be called when the manager is no longer needed.
        """
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()


# Export all classes
__all__ = [
    "ManagerError",
    "BaseManager",
]
