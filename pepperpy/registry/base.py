"""Base registry functionality for PepperPy.

This module provides the base functionality for registries in PepperPy.
Registries are used to manage and organize components, providers, schemas,
and other objects throughout the framework.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pepperpy.errors.core import PepperPyError
from pepperpy.types import Identifiable
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for registry item types
T = TypeVar("T")


class RegistryError(PepperPyError):
    """Error raised for registry-related issues."""

    pass


class Registry(Identifiable, Generic[T]):
    """Base registry for components in the framework.

    A registry keeps track of components and their implementations.
    It provides methods for registering, retrieving, and listing components.

    Args:
        T: The type of objects that this registry manages
    """

    def __init__(self, registry_name: str, registry_type: str):
        """Initialize the registry.

        Args:
            registry_name: The name of this registry instance
            registry_type: The type of registry (e.g., 'provider', 'schema')
        """
        self._registry_name = registry_name
        self._registry_type = registry_type
        self._registry: Dict[str, T] = {}

    @property
    def id(self) -> str:
        """Get the ID of this registry.

        Returns:
            The registry ID
        """
        return self._registry_name

    @property
    def registry_type(self) -> str:
        """Get the type of this registry.

        Returns:
            The registry type
        """
        return self._registry_type

    def register(self, key: str, item: T) -> None:
        """Register an item with the given key.

        Args:
            key: The key to register the item under
            item: The item to register

        Raises:
            RegistryError: If an item is already registered with the given key
        """
        if key in self._registry:
            raise RegistryError(
                f"Item with key '{key}' is already registered in registry '{self._registry_name}'"
            )
        self._registry[key] = item
        logger.debug(
            f"Registered {self._registry_type} '{key}' in registry '{self._registry_name}'"
        )

    def unregister(self, key: str) -> None:
        """Unregister an item.

        Args:
            key: The key of the item to unregister

        Raises:
            RegistryError: If no item is registered with the given key
        """
        if key not in self._registry:
            raise RegistryError(
                f"No item with key '{key}' is registered in registry '{self._registry_name}'"
            )
        del self._registry[key]
        logger.debug(
            f"Unregistered {self._registry_type} '{key}' from registry '{self._registry_name}'"
        )

    def get(self, key: str) -> Optional[T]:
        """Get an item by key.

        Args:
            key: The key of the item to get

        Returns:
            The item, or None if not found
        """
        return self._registry.get(key)

    def get_or_raise(self, key: str) -> T:
        """Get an item by key, raising an error if not found.

        Args:
            key: The key of the item to get

        Returns:
            The item

        Raises:
            RegistryError: If no item is registered with the given key
        """
        item = self.get(key)
        if item is None:
            raise RegistryError(
                f"No item with key '{key}' is registered in registry '{self._registry_name}'"
            )
        return item

    def list_keys(self) -> List[str]:
        """List all registered keys.

        Returns:
            A list of registered keys
        """
        return list(self._registry.keys())

    def list_items(self) -> List[T]:
        """List all registered items.

        Returns:
            A list of registered items
        """
        return list(self._registry.values())

    def has_key(self, key: str) -> bool:
        """Check if a key is registered.

        Args:
            key: The key to check

        Returns:
            True if the key is registered, False otherwise
        """
        return key in self._registry

    def clear(self) -> None:
        """Clear the registry."""
        self._registry.clear()
        logger.debug(f"Cleared registry '{self._registry_name}'")

    def __len__(self) -> int:
        """Get the number of registered items.

        Returns:
            The number of registered items
        """
        return len(self._registry)


class TypeRegistry(Registry[Type[T]]):
    """Registry for types (classes).

    A type registry keeps track of types and can create instances of these types.
    """

    def create(self, key: str, **kwargs: Any) -> T:
        """Create an instance of a registered type.

        Args:
            key: The key of the type to create an instance of
            **kwargs: Arguments to pass to the constructor

        Returns:
            An instance of the type

        Raises:
            RegistryError: If no type is registered with the given key
        """
        class_type = self.get_or_raise(key)
        return class_type(**kwargs)


# Global registry of registries
registry_of_registries = Registry[Registry[Any]](
    registry_name="registry_of_registries", registry_type="registry"
)
