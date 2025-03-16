"""Core base classes and interfaces for PepperPy.

This module defines the fundamental abstractions used throughout the PepperPy framework,
including protocols, abstract base classes, and manager functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar

from pepperpy.core.errors import PepperPyError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for generic protocols and classes
T = TypeVar("T")
U = TypeVar("U")
P = TypeVar("P", bound="BaseProvider")


# ---- Core Protocols ----


class Resource:
    """Placeholder for Resource class to avoid circular imports."""

    pass


class Result:
    """Placeholder for Result class to avoid circular imports."""

    pass


class Processor(Protocol):
    """Protocol for processors.

    A processor is responsible for processing data and returning a result.
    """

    def process(self, data: Any) -> Any:
        """Process data and return a result.

        Args:
            data: The data to process

        Returns:
            The processed data
        """
        ...


class Configurable(Protocol):
    """Protocol for configurable components.

    A configurable component can be configured with key-value pairs.
    """

    def configure(self, **kwargs: Any) -> "Configurable":
        """Configure the component with key-value pairs.

        Args:
            **kwargs: Configuration key-value pairs

        Returns:
            The configured component
        """
        ...


class Initializable(Protocol):
    """Protocol for initializable components.

    An initializable component can be initialized before use.
    """

    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        """
        ...


class Cleanable(Protocol):
    """Protocol for cleanable components.

    A cleanable component can be cleaned up after use.
    """

    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be called after using the component.
        """
        ...


class Serializable(Protocol):
    """Protocol for serializable components.

    A serializable component can be converted to and from a dictionary.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert the component to a dictionary.

        Returns:
            A dictionary representation of the component
        """
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable":
        """Create a component from a dictionary.

        Args:
            data: A dictionary representation of the component

        Returns:
            A new component instance
        """
        ...


class Identifiable(Protocol):
    """Protocol for identifiable components.

    An identifiable component has a unique identifier.
    """

    @property
    def id(self) -> str:
        """Get the unique identifier of the component.

        Returns:
            The unique identifier
        """
        ...


# ---- Abstract Base Classes ----


class Provider(ABC):
    """Base class for providers.

    A provider is responsible for providing a service or resource.
    """

    @abstractmethod
    async def validate(self) -> None:
        """Validate the provider.

        This method should check if the provider is properly configured
        and can provide the service or resource.

        Raises:
            ValueError: If the provider is not properly configured
        """
        pass


class ProviderCapability:
    """Capability of a provider.

    A capability represents a feature or functionality that a provider supports.
    """

    def __init__(
        self, name: str, description: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a provider capability.

        Args:
            name: The name of the capability
            description: A description of the capability
            metadata: Additional metadata for the capability
        """
        self.name = name
        self.description = description
        self.metadata = metadata or {}


class ProviderConfig:
    """Configuration for a provider.

    A provider configuration contains the settings needed to create and
    configure a provider.
    """

    def __init__(self, provider_type: str, settings: Optional[Dict[str, Any]] = None):
        """Initialize a provider configuration.

        Args:
            provider_type: The type of the provider
            settings: The settings for the provider
        """
        self.provider_type = provider_type
        self.settings = settings or {}


class ResourceProvider(Provider):
    """Base class for resource providers.

    Resource providers are responsible for managing resources.
    """

    @abstractmethod
    async def get(self, resource_id: str) -> Resource:
        """Get a resource by ID.

        Args:
            resource_id: The ID of the resource to get

        Returns:
            The resource

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        pass

    @abstractmethod
    async def create(self, resource: Resource) -> Resource:
        """Create a resource.

        Args:
            resource: The resource to create

        Returns:
            The created resource
        """
        pass

    @abstractmethod
    async def update(self, resource: Resource) -> Resource:
        """Update a resource.

        Args:
            resource: The resource to update

        Returns:
            The updated resource

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        pass

    @abstractmethod
    async def delete(self, resource_id: str) -> None:
        """Delete a resource.

        Args:
            resource_id: The ID of the resource to delete

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        pass

    @abstractmethod
    async def list(self, **kwargs: Any) -> List[Resource]:
        """List resources.

        Args:
            **kwargs: Filtering parameters

        Returns:
            A list of resources
        """
        pass


class Transformer(Processor):
    """Base class for transformers.

    A transformer transforms data from one form to another.
    """

    @abstractmethod
    async def transform(self, data: T) -> U:
        """Transform data.

        Args:
            data: The data to transform

        Returns:
            The transformed data
        """
        pass

    async def process(self, data: Any) -> Any:
        """Process data by transforming it.

        Args:
            data: The data to process

        Returns:
            The processed data
        """
        return await self.transform(data)


class Analyzer(Processor):
    """Base class for analyzers.

    An analyzer analyzes data and returns a result.
    """

    @abstractmethod
    async def analyze(self, data: T) -> Result:
        """Analyze data.

        Args:
            data: The data to analyze

        Returns:
            The analysis result
        """
        pass

    async def process(self, data: Any) -> Any:
        """Process data by analyzing it.

        Args:
            data: The data to process

        Returns:
            The processed data
        """
        return await self.analyze(data)


class Generator(Processor):
    """Base class for generators.

    A generator generates data based on input parameters.
    """

    @abstractmethod
    async def generate(self, **kwargs: Any) -> T:
        """Generate data.

        Args:
            **kwargs: Generation parameters

        Returns:
            The generated data
        """
        pass

    async def process(self, data: Any) -> Any:
        """Process data by using it as parameters for generation.

        Args:
            data: The data to process

        Returns:
            The processed data
        """
        if isinstance(data, dict):
            return await self.generate(**data)
        return await self.generate(data=data)


class Validator(Processor):
    """Base class for validators.

    A validator validates data and returns a boolean result.
    """

    @abstractmethod
    async def validate(self, data: T) -> bool:
        """Validate data.

        Args:
            data: The data to validate

        Returns:
            True if the data is valid, False otherwise
        """
        pass

    async def process(self, data: Any) -> Any:
        """Process data by validating it.

        Args:
            data: The data to process

        Returns:
            The validation result
        """
        return await self.validate(data)


# ---- Base Provider ----


class BaseProvider(Provider):
    """Base class for all providers in the framework.

    A provider is responsible for providing a specific service or resource.
    """

    def __init__(self, name: str, **kwargs: Any):
        """Initialize the provider.

        Args:
            name: The name of this provider instance
            **kwargs: Additional provider configuration
        """
        self.name = name
        self.config = kwargs

    async def validate(self) -> None:
        """Validate the provider configuration.

        Raises:
            ValueError: If the provider is not properly configured
        """
        # Base implementation does nothing
        pass

    async def close(self) -> None:
        """Close the provider and release resources.

        This method should be called when the provider is no longer needed.
        """
        # Base implementation does nothing
        pass


# ---- Manager Classes ----


class ManagerError(PepperPyError):
    """Error raised for manager-related issues."""

    pass


class Registry(Generic[T]):
    """Registry for storing and retrieving components by key.

    A registry is a simple key-value store for components.
    """

    def __init__(self, registry_name: str, registry_type: str):
        """Initialize the registry.

        Args:
            registry_name: The name of this registry instance
            registry_type: The type of registry (e.g., 'provider', 'component')
        """
        self._registry_name = registry_name
        self._registry_type = registry_type
        self._registry: Dict[str, T] = {}

    def register(self, key: str, item: T) -> None:
        """Register an item with a key.

        Args:
            key: The key to register the item with
            item: The item to register

        Raises:
            ValueError: If the key is already registered
        """
        if key in self._registry:
            raise ValueError(f"Key '{key}' is already registered")
        self._registry[key] = item

    def unregister(self, key: str) -> None:
        """Unregister an item by key.

        Args:
            key: The key to unregister

        Raises:
            ValueError: If the key is not registered
        """
        if key not in self._registry:
            raise ValueError(f"Key '{key}' is not registered")
        del self._registry[key]

    def get(self, key: str) -> Optional[T]:
        """Get an item by key.

        Args:
            key: The key to get the item for

        Returns:
            The item, or None if the key is not registered
        """
        return self._registry.get(key)

    def list(self) -> List[str]:
        """List all registered keys.

        Returns:
            A list of registered keys
        """
        return list(self._registry.keys())

    def clear(self) -> None:
        """Clear the registry."""
        self._registry.clear()


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
