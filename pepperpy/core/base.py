"""Core Base Module.

This module defines the core interfaces, types and components used throughout
the PepperPy framework.

Example:
    >>> from pepperpy.core.base import Component
    >>> class MyComponent(Component):
    ...     async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    ...         return {"result": inputs["data"] * 2}
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)

from pepperpy.core.errors import (
    PepperpyError,
)

T = TypeVar("T")

# Common Types
Metadata = Dict[str, Any]
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], list]
JsonDict = Dict[str, JsonValue]
JsonType = Union[Dict[str, Any], List[Any]]

# Component types
ComponentType = str
ComponentConfigType = Dict[str, Any]

# Document types
DocumentType = str
DocumentConfigType = Dict[str, Any]

# Result types
ResultType = Dict[str, Any]
ResultListType = List[ResultType]


class ComponentError(PepperpyError):
    """Error raised by components."""

    pass


# Core Protocols and Base Classes
class Component(Protocol):
    """Base protocol for all workflow components."""

    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and return outputs.

        Args:
            inputs: Input data

        Returns:
            Output data
        """
        return {}  # Default empty response


class BaseComponent:
    """Base class for all components.

    This class provides the foundation for all components in the PepperPy framework.
    Components are the building blocks of workflows and can be used to process data
    in a pipeline.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize component.

        Args:
            **kwargs: Component options
        """
        self.options = kwargs

    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs.

        Args:
            inputs: Input data

        Returns:
            Output data
        """
        return {}  # Default empty response


class ComponentRegistry:
    """Registry for workflow components."""

    _components: Dict[str, Type[BaseComponent]] = {}

    @classmethod
    def register(cls, name: str) -> Any:
        """Register a component.

        Args:
            name: Component name

        Returns:
            Decorator function
        """

        def decorator(component: Type[BaseComponent]) -> Type[BaseComponent]:
            cls._components[name] = component
            return component

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseComponent]]:
        """Get a component by name.

        Args:
            name: Component name

        Returns:
            Component class or None if not found
        """
        return cls._components.get(name)

    @classmethod
    def list(cls) -> List[str]:
        """List registered components.

        Returns:
            List of component names
        """
        return list(cls._components.keys())


# Result Types
@dataclass
class GenerationResult:
    """Result from an LLM generation."""

    text: str
    metadata: Optional[Metadata] = None


@dataclass
class SearchResult:
    """Result from a search operation."""

    document: "Document"
    score: float
    metadata: Optional[Metadata] = None


@dataclass
class Document:
    """A document in the PepperPy framework.

    This class represents a document that can be stored, retrieved, and processed
    by the framework. It includes the document's content, metadata, and embeddings.
    """

    content: str
    metadata: Optional[Metadata] = field(default=None)
    embeddings: Optional[List[float]] = field(default=None)
    id: Optional[str] = field(default=None)


# Core Protocols and Base Classes
class ModelContext(Protocol[T]):
    """Protocol defining the model context interface."""

    @property
    def model(self) -> T:
        """Get the model instance."""
        ...

    @property
    def context(self) -> Dict[str, Any]:
        """Get the context dictionary."""
        ...


class BaseModelContext(ABC):
    """Base implementation of the model context protocol."""

    def __init__(
        self,
        model: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the model context.

        Args:
            model: The model instance.
            context: Optional context dictionary.
        """
        self._model = model
        self._context = context or {}

    @property
    def model(self) -> Any:
        """Get the model instance."""
        return self._model

    @property
    def context(self) -> Dict[str, Any]:
        """Get the context dictionary."""
        return self._context

    def update_context(self, **kwargs: Any) -> None:
        """Update the context with new values.

        Args:
            **kwargs: Key-value pairs to update in the context.
        """
        self._context.update(kwargs)

    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the context.

        Args:
            key: The key to get.
            default: Default value if key doesn't exist.

        Returns:
            The value from the context or the default.
        """
        return self._context.get(key, default)


# Exports
__all__ = [
    # Types
    "Metadata",
    "JsonValue",
    "JsonDict",
    "JsonType",
    "ComponentType",
    "ComponentConfigType",
    "DocumentType",
    "DocumentConfigType",
    "ResultType",
    "ResultListType",
    # Results
    "GenerationResult",
    "SearchResult",
    "Document",
    # Errors
    "PepperpyError",
    "ComponentError",
    # Protocols and Base Classes
    "Component",
    "BaseComponent",
    "ComponentRegistry",
    "ModelContext",
    "BaseModelContext",
]
