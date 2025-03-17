"""PepperPy Interfaces Module.

This module provides protocol and interface definitions for the PepperPy framework, including:
- Base protocols for common patterns
- Resource management protocols
- Design pattern protocols
- Data management protocols
- Service management protocols

The interfaces module is designed to define the contracts that components in the
framework must adhere to, enabling loose coupling and dependency injection.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from pepperpy.types import JsonValue

# Type variable for parametric protocols
T = TypeVar("T")
U = TypeVar("U")
R = TypeVar("R")


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an identifier.

    This protocol defines the interface for objects that have a unique identifier.
    """

    @property
    def id(self) -> str:
        """Get the identifier.

        Returns:
            The identifier
        """
        ...


@runtime_checkable
class Describable(Protocol):
    """Protocol for objects that have a description.

    This protocol defines the interface for objects that have a human-readable
    description.
    """

    @property
    def description(self) -> str:
        """Get the description.

        Returns:
            The description
        """
        ...


@runtime_checkable
class Nameable(Protocol):
    """Protocol for objects that have a name.

    This protocol defines the interface for objects that have a human-readable name.
    """

    @property
    def name(self) -> str:
        """Get the name.

        Returns:
            The name
        """
        ...


@runtime_checkable
class Versioned(Protocol):
    """Protocol for objects that have a version.

    This protocol defines the interface for objects that have a version number.
    """

    @property
    def version(self) -> str:
        """Get the version.

        Returns:
            The version
        """
        ...


@runtime_checkable
class Metadata(Protocol):
    """Protocol for objects that have metadata.

    This protocol defines the interface for objects that have additional metadata.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata.

        Returns:
            The metadata
        """
        ...


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized.

    This protocol defines the interface for objects that can be serialized to
    and deserialized from a dictionary.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary.

        Returns:
            The object as a dictionary
        """
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable":
        """Create an object from a dictionary.

        Args:
            data: The dictionary to create the object from

        Returns:
            The created object
        """
        ...


@runtime_checkable
class Resettable(Protocol):
    """Protocol for objects that can be reset.

    This protocol defines the interface for objects that can be reset to their
    initial state.
    """

    def reset(self) -> None:
        """Reset the object to its initial state."""
        ...


@runtime_checkable
class Closable(Protocol):
    """Protocol for objects that can be closed.

    This protocol defines the interface for objects that can be closed, such as
    resources that need to be released.
    """

    def close(self) -> None:
        """Close the object, releasing any resources."""
        ...


@runtime_checkable
class AsyncClosable(Protocol):
    """Protocol for objects that can be closed asynchronously.

    This protocol defines the interface for objects that can be closed
    asynchronously, such as resources that need to be released.
    """

    async def aclose(self) -> None:
        """Close the object asynchronously, releasing any resources."""
        ...


@runtime_checkable
class Configurable(Protocol):
    """Protocol for objects that can be configured.

    This protocol defines the interface for objects that can be configured with
    a dictionary of configuration values.
    """

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the object.

        Args:
            config: The configuration values
        """
        ...


@runtime_checkable
class AsyncConfigurable(Protocol):
    """Protocol for objects that can be configured asynchronously.

    This protocol defines the interface for objects that can be configured
    asynchronously with a dictionary of configuration values.
    """

    async def aconfigure(self, config: Dict[str, Any]) -> None:
        """Configure the object asynchronously.

        Args:
            config: The configuration values
        """
        ...


@runtime_checkable
class Initializable(Protocol):
    """Protocol for objects that can be initialized.

    This protocol defines the interface for objects that can be initialized
    before use.
    """

    def initialize(self) -> None:
        """Initialize the object."""
        ...


@runtime_checkable
class AsyncInitializable(Protocol):
    """Protocol for objects that can be initialized asynchronously.

    This protocol defines the interface for objects that can be initialized
    asynchronously before use.
    """

    async def ainitialize(self) -> None:
        """Initialize the object asynchronously."""
        ...


@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated.

    This protocol defines the interface for objects that can be validated to
    ensure they are in a valid state.
    """

    def validate(self) -> None:
        """Validate the object.

        Raises:
            ValidationError: If validation fails
        """
        ...


@runtime_checkable
class AsyncValidatable(Protocol):
    """Protocol for objects that can be validated asynchronously.

    This protocol defines the interface for objects that can be validated
    asynchronously to ensure they are in a valid state.
    """

    async def avalidate(self) -> None:
        """Validate the object asynchronously.

        Raises:
            ValidationError: If validation fails
        """
        ...


@runtime_checkable
class Observable(Protocol):
    """Protocol for objects that can be observed.

    This protocol defines the interface for objects that can be observed, allowing
    observers to be notified of changes.
    """

    def add_observer(self, observer: "Observer") -> None:
        """Add an observer.

        Args:
            observer: The observer to add
        """
        ...

    def remove_observer(self, observer: "Observer") -> None:
        """Remove an observer.

        Args:
            observer: The observer to remove
        """
        ...

    def notify_observers(self, event: str, data: Any = None) -> None:
        """Notify observers of an event.

        Args:
            event: The event to notify observers of
            data: Additional data about the event
        """
        ...


@runtime_checkable
class Observer(Protocol):
    """Protocol for observers.

    This protocol defines the interface for observers that can be notified of
    changes to an observable object.
    """

    def update(self, observable: Observable, event: str, data: Any = None) -> None:
        """Update the observer.

        Args:
            observable: The observable object that changed
            event: The event that occurred
            data: Additional data about the event
        """
        ...


@runtime_checkable
class AsyncObserver(Protocol):
    """Protocol for asynchronous observers.

    This protocol defines the interface for observers that can be notified
    asynchronously of changes to an observable object.
    """

    async def aupdate(
        self, observable: Observable, event: str, data: Any = None
    ) -> None:
        """Update the observer asynchronously.

        Args:
            observable: The observable object that changed
            event: The event that occurred
            data: Additional data about the event
        """
        ...


@runtime_checkable
class Provider(Protocol[T]):
    """Protocol for providers.

    This protocol defines the interface for providers that can provide a value.
    """

    def provide(self) -> T:
        """Provide a value.

        Returns:
            The provided value
        """
        ...


@runtime_checkable
class AsyncProvider(Protocol[T]):
    """Protocol for asynchronous providers.

    This protocol defines the interface for providers that can provide a value
    asynchronously.
    """

    async def aprovide(self) -> T:
        """Provide a value asynchronously.

        Returns:
            The provided value
        """
        ...


@runtime_checkable
class Factory(Protocol[T]):
    """Protocol for factories.

    This protocol defines the interface for factories that can create objects.
    """

    def create(self, *args: Any, **kwargs: Any) -> T:
        """Create an object.

        Args:
            *args: Positional arguments to pass to the object constructor
            **kwargs: Keyword arguments to pass to the object constructor

        Returns:
            The created object
        """
        ...


@runtime_checkable
class AsyncFactory(Protocol[T]):
    """Protocol for asynchronous factories.

    This protocol defines the interface for factories that can create objects
    asynchronously.
    """

    async def acreate(self, *args: Any, **kwargs: Any) -> T:
        """Create an object asynchronously.

        Args:
            *args: Positional arguments to pass to the object constructor
            **kwargs: Keyword arguments to pass to the object constructor

        Returns:
            The created object
        """
        ...


@runtime_checkable
class Cache(Protocol[T]):
    """Protocol for caches.

    This protocol defines the interface for caches that can store and retrieve
    values.
    """

    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache
        """
        ...

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        ...

    def delete(self, key: str) -> None:
        """Delete a value from the cache.

        Args:
            key: The key to delete the value for
        """
        ...

    def clear(self) -> None:
        """Clear the cache."""
        ...


@runtime_checkable
class AsyncCache(Protocol[T]):
    """Protocol for asynchronous caches.

    This protocol defines the interface for caches that can store and retrieve
    values asynchronously.
    """

    async def aget(self, key: str) -> Optional[T]:
        """Get a value from the cache asynchronously.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache
        """
        ...

    async def aset(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a value in the cache asynchronously.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        ...

    async def adelete(self, key: str) -> None:
        """Delete a value from the cache asynchronously.

        Args:
            key: The key to delete the value for
        """
        ...

    async def aclear(self) -> None:
        """Clear the cache asynchronously."""
        ...


@runtime_checkable
class Registry(Protocol[T]):
    """Protocol for registries.

    This protocol defines the interface for registries that can register and
    retrieve objects.
    """

    def register(self, id: str, obj: T) -> None:
        """Register an object.

        Args:
            id: The ID to register the object under
            obj: The object to register
        """
        ...

    def unregister(self, id: str) -> None:
        """Unregister an object.

        Args:
            id: The ID to unregister the object for
        """
        ...

    def get(self, id: str) -> T:
        """Get an object.

        Args:
            id: The ID to get the object for

        Returns:
            The object

        Raises:
            NotFoundError: If the object is not registered
        """
        ...

    def list(self) -> List[str]:
        """List all registered object IDs.

        Returns:
            A list of registered object IDs
        """
        ...

    def clear(self) -> None:
        """Clear the registry."""
        ...


@runtime_checkable
class AsyncRegistry(Protocol[T]):
    """Protocol for asynchronous registries.

    This protocol defines the interface for registries that can register and
    retrieve objects asynchronously.
    """

    async def aregister(self, id: str, obj: T) -> None:
        """Register an object asynchronously.

        Args:
            id: The ID to register the object under
            obj: The object to register
        """
        ...

    async def aunregister(self, id: str) -> None:
        """Unregister an object asynchronously.

        Args:
            id: The ID to unregister the object for
        """
        ...

    async def aget(self, id: str) -> T:
        """Get an object asynchronously.

        Args:
            id: The ID to get the object for

        Returns:
            The object

        Raises:
            NotFoundError: If the object is not registered
        """
        ...

    async def alist(self) -> List[str]:
        """List all registered object IDs asynchronously.

        Returns:
            A list of registered object IDs
        """
        ...

    async def aclear(self) -> None:
        """Clear the registry asynchronously."""
        ...


@runtime_checkable
class Repository(Protocol[T]):
    """Protocol for repositories.

    This protocol defines the interface for repositories that can store and
    retrieve objects.
    """

    def add(self, obj: T) -> None:
        """Add an object to the repository.

        Args:
            obj: The object to add
        """
        ...

    def remove(self, obj: T) -> None:
        """Remove an object from the repository.

        Args:
            obj: The object to remove
        """
        ...

    def get(self, id: str) -> T:
        """Get an object from the repository.

        Args:
            id: The ID of the object to get

        Returns:
            The object

        Raises:
            NotFoundError: If the object is not in the repository
        """
        ...

    def find(self, **criteria: Any) -> List[T]:
        """Find objects in the repository.

        Args:
            **criteria: The criteria to search for

        Returns:
            A list of matching objects
        """
        ...

    def list(self) -> List[T]:
        """List all objects in the repository.

        Returns:
            A list of all objects in the repository
        """
        ...

    def clear(self) -> None:
        """Clear the repository."""
        ...


@runtime_checkable
class AsyncRepository(Protocol[T]):
    """Protocol for asynchronous repositories.

    This protocol defines the interface for repositories that can store and
    retrieve objects asynchronously.
    """

    async def aadd(self, obj: T) -> None:
        """Add an object to the repository asynchronously.

        Args:
            obj: The object to add
        """
        ...

    async def aremove(self, obj: T) -> None:
        """Remove an object from the repository asynchronously.

        Args:
            obj: The object to remove
        """
        ...

    async def aget(self, id: str) -> T:
        """Get an object from the repository asynchronously.

        Args:
            id: The ID of the object to get

        Returns:
            The object

        Raises:
            NotFoundError: If the object is not in the repository
        """
        ...

    async def afind(self, **criteria: Any) -> List[T]:
        """Find objects in the repository asynchronously.

        Args:
            **criteria: The criteria to search for

        Returns:
            A list of matching objects
        """
        ...

    async def alist(self) -> List[T]:
        """List all objects in the repository asynchronously.

        Returns:
            A list of all objects in the repository
        """
        ...

    async def aclear(self) -> None:
        """Clear the repository asynchronously."""
        ...


@runtime_checkable
class Service(Protocol):
    """Protocol for services.

    This protocol defines the interface for services that can be started and stopped.
    """

    def start(self) -> None:
        """Start the service."""
        ...

    def stop(self) -> None:
        """Stop the service."""
        ...

    @property
    def is_running(self) -> bool:
        """Check if the service is running.

        Returns:
            True if the service is running, False otherwise
        """
        ...


@runtime_checkable
class AsyncService(Protocol):
    """Protocol for asynchronous services.

    This protocol defines the interface for services that can be started and stopped
    asynchronously.
    """

    async def astart(self) -> None:
        """Start the service asynchronously."""
        ...

    async def astop(self) -> None:
        """Stop the service asynchronously."""
        ...

    @property
    def is_running(self) -> bool:
        """Check if the service is running.

        Returns:
            True if the service is running, False otherwise
        """
        ...


@runtime_checkable
class Processor(Protocol[T, U]):
    """Protocol for processors.

    This protocol defines the interface for processors that can process an input
    value and produce an output value.
    """

    def process(self, input_value: T) -> U:
        """Process an input value.

        Args:
            input_value: The input value to process

        Returns:
            The processed output value
        """
        ...


@runtime_checkable
class AsyncProcessor(Protocol[T, U]):
    """Protocol for asynchronous processors.

    This protocol defines the interface for processors that can process an input
    value and produce an output value asynchronously.
    """

    async def aprocess(self, input_value: T) -> U:
        """Process an input value asynchronously.

        Args:
            input_value: The input value to process

        Returns:
            The processed output value
        """
        ...


@runtime_checkable
class Handler(Protocol[T]):
    """Protocol for handlers.

    This protocol defines the interface for handlers that can handle a value.
    """

    def handle(self, value: T) -> None:
        """Handle a value.

        Args:
            value: The value to handle
        """
        ...


@runtime_checkable
class AsyncHandler(Protocol[T]):
    """Protocol for asynchronous handlers.

    This protocol defines the interface for handlers that can handle a value
    asynchronously.
    """

    async def ahandle(self, value: T) -> None:
        """Handle a value asynchronously.

        Args:
            value: The value to handle
        """
        ...


@runtime_checkable
class Iterator(Protocol[T]):
    """Protocol for iterators.

    This protocol defines the interface for iterators that can iterate over
    a sequence of values.
    """

    def __iter__(self) -> "Iterator[T]":
        """Get an iterator.

        Returns:
            The iterator
        """
        ...

    def __next__(self) -> T:
        """Get the next value.

        Returns:
            The next value

        Raises:
            StopIteration: If there are no more values
        """
        ...


@runtime_checkable
class AsyncIterator(Protocol[T]):
    """Protocol for asynchronous iterators.

    This protocol defines the interface for iterators that can iterate over
    a sequence of values asynchronously.
    """

    def __aiter__(self) -> "AsyncIterator[T]":
        """Get an asynchronous iterator.

        Returns:
            The asynchronous iterator
        """
        ...

    async def __anext__(self) -> T:
        """Get the next value asynchronously.

        Returns:
            The next value

        Raises:
            StopAsyncIteration: If there are no more values
        """
        ...


@runtime_checkable
class Adapter(Protocol[T, U]):
    """Protocol for adapters.

    This protocol defines the interface for adapters that can adapt a value from
    one type to another.
    """

    def adapt(self, value: T) -> U:
        """Adapt a value.

        Args:
            value: The value to adapt

        Returns:
            The adapted value
        """
        ...


@runtime_checkable
class AsyncAdapter(Protocol[T, U]):
    """Protocol for asynchronous adapters.

    This protocol defines the interface for adapters that can adapt a value from
    one type to another asynchronously.
    """

    async def aadapt(self, value: T) -> U:
        """Adapt a value asynchronously.

        Args:
            value: The value to adapt

        Returns:
            The adapted value
        """
        ...


@runtime_checkable
class Converter(Protocol[T, U]):
    """Protocol for converters.

    This protocol defines the interface for converters that can convert a value
    from one type to another, and back again.
    """

    def convert_to(self, value: T) -> U:
        """Convert a value to the target type.

        Args:
            value: The value to convert

        Returns:
            The converted value
        """
        ...

    def convert_from(self, value: U) -> T:
        """Convert a value from the target type.

        Args:
            value: The value to convert

        Returns:
            The converted value
        """
        ...


@runtime_checkable
class AsyncConverter(Protocol[T, U]):
    """Protocol for asynchronous converters.

    This protocol defines the interface for converters that can convert a value
    from one type to another, and back again, asynchronously.
    """

    async def aconvert_to(self, value: T) -> U:
        """Convert a value to the target type asynchronously.

        Args:
            value: The value to convert

        Returns:
            The converted value
        """
        ...

    async def aconvert_from(self, value: U) -> T:
        """Convert a value from the target type asynchronously.

        Args:
            value: The value to convert

        Returns:
            The converted value
        """
        ...


@runtime_checkable
class JSONSerializable(Protocol):
    """Protocol for objects that can be serialized to JSON.

    This protocol defines the interface for objects that can be serialized to and
    deserialized from JSON.
    """

    def to_json(self) -> JsonValue:
        """Convert the object to JSON.

        Returns:
            The object as JSON
        """
        ...

    @classmethod
    def from_json(cls, data: JsonValue) -> "JSONSerializable":
        """Create an object from JSON.

        Args:
            data: The JSON to create the object from

        Returns:
            The created object
        """
        ...


@runtime_checkable
class Filter(Protocol[T]):
    """Protocol for filters.

    This protocol defines the interface for filters that can filter values.
    """

    def filter(self, value: T) -> bool:
        """Filter a value.

        Args:
            value: The value to filter

        Returns:
            True if the value should be included, False otherwise
        """
        ...


@runtime_checkable
class AsyncFilter(Protocol[T]):
    """Protocol for asynchronous filters.

    This protocol defines the interface for filters that can filter values
    asynchronously.
    """

    async def afilter(self, value: T) -> bool:
        """Filter a value asynchronously.

        Args:
            value: The value to filter

        Returns:
            True if the value should be included, False otherwise
        """
        ...


@runtime_checkable
class Validator(Protocol[T]):
    """Protocol for validators.

    This protocol defines the interface for validators that can validate values.
    """

    def validate(self, value: T) -> None:
        """Validate a value.

        Args:
            value: The value to validate

        Raises:
            ValidationError: If validation fails
        """
        ...


@runtime_checkable
class AsyncValidator(Protocol[T]):
    """Protocol for asynchronous validators.

    This protocol defines the interface for validators that can validate values
    asynchronously.
    """

    async def avalidate(self, value: T) -> None:
        """Validate a value asynchronously.

        Args:
            value: The value to validate

        Raises:
            ValidationError: If validation fails
        """
        ...


# __all__ defines the public API
__all__ = [
    # Basic protocols
    "Identifiable",
    "Describable",
    "Nameable",
    "Versioned",
    "Metadata",
    "Serializable",
    "JSONSerializable",
    "Resettable",
    # Resource management protocols
    "Closable",
    "AsyncClosable",
    "Configurable",
    "AsyncConfigurable",
    "Initializable",
    "AsyncInitializable",
    "Validatable",
    "AsyncValidatable",
    # Design pattern protocols
    "Observable",
    "Observer",
    "AsyncObserver",
    "Provider",
    "AsyncProvider",
    "Factory",
    "AsyncFactory",
    "Adapter",
    "AsyncAdapter",
    "Converter",
    "AsyncConverter",
    # Data management protocols
    "Cache",
    "AsyncCache",
    "Registry",
    "AsyncRegistry",
    "Repository",
    "AsyncRepository",
    # Service management protocols
    "Service",
    "AsyncService",
    # Processing protocols
    "Processor",
    "AsyncProcessor",
    "Handler",
    "AsyncHandler",
    "Iterator",
    "AsyncIterator",
    "Filter",
    "AsyncFilter",
    "Validator",
    "AsyncValidator",
]
