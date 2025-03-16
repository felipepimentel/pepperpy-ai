"""Registry system for PepperPy.

This module provides a centralized registry system for managing components,
providers, types, and other objects throughout the PepperPy framework.

The registry system consists of several registry types:
- Registry: Base registry for general-purpose component registration
- TypeRegistry: Registry for type-safe component registration
- ProviderRegistry: Registry for provider components with hierarchical organization

Example:
    ```python
    # Create a registry for components
    from pepperpy.core.registry import Registry

    # Create a registry for string components
    string_registry = Registry[str]("string_registry", "string")

    # Register components
    string_registry.register("greeting", "Hello, world!")

    # Retrieve components
    greeting = string_registry.get("greeting")
    print(greeting)  # Output: Hello, world!
    ```
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast

from pepperpy.core.base import Identifiable
from pepperpy.core.errors import PepperPyError, ProviderError

# Type variables for registry item types
T = TypeVar("T")
P = TypeVar("P")  # For provider types


# ---- Registry Exceptions ----


class RegistryError(PepperPyError):
    """Error raised for registry-related issues."""

    pass


class ItemNotFoundError(RegistryError):
    """Error raised when an item is not found in a registry."""

    pass


class ProviderNotFoundError(ProviderError):
    """Error raised when a provider is not found in the registry."""

    pass


# ---- Base Registry ----


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
        self._default_key: Optional[str] = None

    @property
    def id(self) -> str:
        """Get the ID of this registry.

        Returns:
            The registry ID in the format '{type}:{name}'
        """
        return f"{self._registry_type}:{self._registry_name}"

    @property
    def registry_type(self) -> str:
        """Get the type of this registry.

        Returns:
            The registry type
        """
        return self._registry_type

    def register(self, key: str, item: T) -> None:
        """Register an item with the registry.

        Args:
            key: The key to register the item under
            item: The item to register

        Raises:
            RegistryError: If registration fails
        """
        try:
            self._registry[key] = item
        except Exception as e:
            raise RegistryError(f"Failed to register item {key}: {e}")

    def unregister(self, key: str) -> None:
        """Unregister an item from the registry.

        Args:
            key: The key of the item to unregister

        Raises:
            RegistryError: If unregistration fails
            ItemNotFoundError: If the item is not found
        """
        try:
            if key not in self._registry:
                raise ItemNotFoundError(f"Item {key} not found")
            del self._registry[key]
            if self._default_key == key:
                self._default_key = None
        except ItemNotFoundError:
            raise
        except Exception as e:
            raise RegistryError(f"Failed to unregister item {key}: {e}")

    def get(self, key: str) -> Optional[T]:
        """Get an item from the registry.

        Args:
            key: The key of the item to get

        Returns:
            The item, or None if not found
        """
        return self._registry.get(key)

    def get_or_raise(self, key: str) -> T:
        """Get an item from the registry, raising an error if not found.

        Args:
            key: The key of the item to get

        Returns:
            The item

        Raises:
            ItemNotFoundError: If the item is not found
        """
        item = self.get(key)
        if item is None:
            raise ItemNotFoundError(f"Item {key} not found")
        return item

    def list_keys(self) -> List[str]:
        """List all keys in the registry.

        Returns:
            List of keys
        """
        return list(self._registry.keys())

    def list_items(self) -> List[T]:
        """List all items in the registry.

        Returns:
            List of items
        """
        return list(self._registry.values())

    def has_key(self, key: str) -> bool:
        """Check if a key exists in the registry.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._registry

    def clear(self) -> None:
        """Clear the registry."""
        self._registry.clear()
        self._default_key = None

    def __len__(self) -> int:
        """Get the number of items in the registry.

        Returns:
            Number of items
        """
        return len(self._registry)

    def set_default(self, key: str) -> None:
        """Set the default key for the registry.

        Args:
            key: The key to set as default

        Raises:
            ItemNotFoundError: If the key does not exist in the registry
        """
        if key not in self._registry:
            raise ItemNotFoundError(f"Cannot set default: item {key} not found")
        self._default_key = key

    def get_default_key(self) -> Optional[str]:
        """Get the default key for the registry.

        Returns:
            The default key, or None if not set
        """
        return self._default_key

    def get_default(self) -> Optional[T]:
        """Get the default item from the registry.

        Returns:
            The default item, or None if not set
        """
        if self._default_key is None:
            return None
        return self._registry.get(self._default_key)


# ---- Type Registry ----


class TypeRegistry(Registry[Type[T]]):
    """Registry for type-safe components.

    A type registry ensures that registered components match the expected type.
    It provides methods for registering, retrieving, and listing components.

    Args:
        T: The type of objects that this registry manages
    """

    def create(self, key: str, **kwargs: Any) -> T:
        """Create an instance of a registered type.

        Args:
            key: The key of the type to create
            **kwargs: Arguments to pass to the constructor

        Returns:
            An instance of the registered type

        Raises:
            ItemNotFoundError: If the type is not found
            RegistryError: If instance creation fails
        """
        item_type = self.get_or_raise(key)
        try:
            return item_type(**kwargs)
        except Exception as e:
            raise RegistryError(f"Failed to create instance of {key}: {e}")


# ---- Provider Registry ----


class ProviderRegistry(Registry[Dict[str, Type[P]]]):
    """Registry for provider components.

    A provider registry organizes providers by type and name.
    It provides methods for registering, retrieving, and creating providers.

    Args:
        P: The base provider type
    """

    def register_provider(
        self, provider_type: str, name: str, provider_class: Type[P]
    ) -> None:
        """Register a provider class.

        Args:
            provider_type: The type of the provider
            name: The name of the provider
            provider_class: The provider class to register

        Raises:
            RegistryError: If registration fails
        """
        try:
            providers = self.get(provider_type)
            if providers is None:
                providers = {}
                self.register(provider_type, providers)
            providers[name] = provider_class
        except Exception as e:
            raise RegistryError(
                f"Failed to register provider {provider_type}:{name}: {e}"
            )

    def get_provider_class(self, provider_type: str, name: str) -> Type[P]:
        """Get a provider class.

        Args:
            provider_type: The type of the provider
            name: The name of the provider

        Returns:
            The provider class

        Raises:
            ProviderNotFoundError: If the provider is not found
        """
        providers = self.get(provider_type)
        if providers is None or name not in providers:
            raise ProviderNotFoundError(f"Provider {provider_type}:{name} not found")
        return providers[name]

    def create_provider(self, provider_type: str, name: str, **kwargs: Any) -> P:
        """Create a provider instance.

        Args:
            provider_type: The type of the provider
            name: The name of the provider
            **kwargs: Arguments to pass to the provider constructor

        Returns:
            A provider instance

        Raises:
            ProviderNotFoundError: If the provider is not found
            RegistryError: If provider creation fails
        """
        provider_class = self.get_provider_class(provider_type, name)
        try:
            return provider_class(**kwargs)
        except Exception as e:
            raise RegistryError(
                f"Failed to create provider {provider_type}:{name}: {e}"
            )

    def list_providers(
        self, provider_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List providers in the registry.

        Args:
            provider_type: Optional provider type to filter by

        Returns:
            Dictionary mapping provider types to lists of provider names
        """
        result: Dict[str, List[str]] = {}
        if provider_type is not None:
            providers = self.get(provider_type)
            if providers is not None:
                result[provider_type] = list(providers.keys())
        else:
            for type_key in self.list_keys():
                providers = cast(Dict[str, Type[P]], self.get(type_key))
                result[type_key] = list(providers.keys())
        return result


# ---- Global Registry Instances ----


# Registry of all registries
registry_of_registries = Registry[Registry[Any]](
    registry_name="registry_of_registries", registry_type="meta"
)

# Registry for provider types
provider_registry = TypeRegistry[Any](
    registry_name="provider_registry", registry_type="provider"
)

# Register the registries in the registry of registries
registry_of_registries.register("registry_of_registries", registry_of_registries)
registry_of_registries.register("provider_registry", provider_registry)


# ---- Provider Registry Functions ----


def register_provider(provider_type: str, provider_class: Type[Any]) -> None:
    """Register a provider class for a provider type.

    Args:
        provider_type: The type of the provider
        provider_class: The provider class to register

    Raises:
        RegistryError: If a provider class is already registered for the provider type
    """
    provider_registry.register(provider_type, provider_class)


def get_provider_class(provider_type: str) -> Optional[Type[Any]]:
    """Get the provider class for a provider type.

    Args:
        provider_type: The type of the provider

    Returns:
        The provider class, or None if not found
    """
    return provider_registry.get(provider_type)


def create_provider(provider_type: str, **kwargs: Any) -> Any:
    """Create a provider instance from a provider type and settings.

    Args:
        provider_type: The type of the provider
        **kwargs: Provider-specific configuration

    Returns:
        A provider instance

    Raises:
        RegistryError: If the provider type is not registered or creation fails
    """
    provider_class = get_provider_class(provider_type)
    if provider_class is None:
        raise RegistryError(f"Provider type '{provider_type}' is not registered")
    try:
        return provider_class(**kwargs)
    except Exception as e:
        raise RegistryError(f"Failed to create provider {provider_type}: {e}")


def list_provider_types() -> List[str]:
    """List all registered provider types.

    Returns:
        A list of registered provider types
    """
    return provider_registry.list_keys()


# Export all classes and functions
__all__ = [
    # Exceptions
    "RegistryError",
    "ItemNotFoundError",
    "ProviderNotFoundError",
    # Registry classes
    "Registry",
    "TypeRegistry",
    "ProviderRegistry",
    # Global registry instances
    "registry_of_registries",
    "provider_registry",
    # Provider registry functions
    "register_provider",
    "get_provider_class",
    "create_provider",
    "list_provider_types",
]
