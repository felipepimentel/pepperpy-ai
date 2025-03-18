"""Essential base interfaces and classes for the PepperPy framework.

This module defines the core interfaces and abstract classes that form the
foundation of the PepperPy framework. These components are designed to be
minimal, stable, and reusable across all other modules.
"""

from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar('T')
ConfigType = Dict[str, Any]

@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have a unique identifier."""
    
    @property
    def id(self) -> str:
        """Return the unique identifier for this object."""
        ...

@runtime_checkable
class Initializable(Protocol):
    """Protocol for objects that require initialization."""
    
    async def initialize(self) -> None:
        """Initialize the object."""
        ...

@runtime_checkable
class Configurable(Protocol):
    """Protocol for objects that can be configured."""
    
    def configure(self, config: ConfigType) -> None:
        """Configure the object with the provided configuration."""
        ...

@runtime_checkable
class Disposable(Protocol):
    """Protocol for objects that need to be disposed of."""
    
    async def dispose(self) -> None:
        """Release resources held by this object."""
        ...

@runtime_checkable
class Resource(Initializable, Disposable, Protocol):
    """Protocol for objects that represent a managed resource."""
    
    @property
    def is_initialized(self) -> bool:
        """Return whether the resource has been initialized."""
        ...

@runtime_checkable
class Provider(Protocol[T]):
    """Protocol for objects that provide a specific type of value."""
    
    async def provide(self) -> T:
        """Provide an instance of the specified type."""
        ...

@runtime_checkable
class Consumer(Protocol[T]):
    """Protocol for objects that consume a specific type of value."""
    
    async def consume(self, value: T) -> None:
        """Consume an instance of the specified type."""
        ...

@runtime_checkable
class Processor(Protocol[T]):
    """Protocol for objects that process a specific type of value."""
    
    async def process(self, value: T) -> T:
        """Process an instance of the specified type and return a new instance."""
        ...

class BaseComponent(Initializable, Configurable, Disposable):
    """Base class for components in the PepperPy framework."""
    
    def __init__(self, config: Optional[ConfigType] = None):
        """Initialize the component with the provided configuration."""
        self._initialized = False
        self._config: ConfigType = {}
        
        if config:
            self.configure(config)
    
    @property
    def is_initialized(self) -> bool:
        """Return whether the component has been initialized."""
        return self._initialized
    
    def configure(self, config: ConfigType) -> None:
        """Configure the component with the provided configuration."""
        self._config.update(config)
    
    async def initialize(self) -> None:
        """Initialize the component."""
        self._initialized = True
    
    async def dispose(self) -> None:
        """Release resources held by this component."""
        self._initialized = False
