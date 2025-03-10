"""Core interfaces for PepperPy.

This module defines core interfaces used throughout the PepperPy framework,
including protocols and abstract base classes for common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

# Define forward references to avoid circular imports
T = TypeVar("T")
U = TypeVar("U")


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

    Transformers are processors that transform data from one format to another.
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


class Analyzer(Processor):
    """Base class for analyzers.

    Analyzers are processors that analyze data and extract information.
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


class Generator(Processor):
    """Base class for generators.

    Generators are processors that generate data.
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


class Validator(Processor):
    """Base class for validators.

    Validators are processors that validate data.
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
