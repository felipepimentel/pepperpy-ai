"""Centralized type definitions for PepperPy.

This module provides common type definitions that are shared across different
modules in the PepperPy framework, ensuring consistency and avoiding duplication.
"""

import inspect
import types
from dataclasses import dataclass, field, is_dataclass
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    runtime_checkable,
)

# ---- Type Variables ----

# Type variables for generic types
T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")
V = TypeVar("V")

# ---- JSON Types ----

# JSON-compatible types
JsonPrimitive = Union[str, int, float, bool, None]
JsonObject = Dict[str, Any]  # Recursive type not expressible cleanly in Python
JsonArray = List[Any]  # Recursive type not expressible cleanly in Python
JsonValue = Union[JsonPrimitive, JsonObject, JsonArray]

# ---- Provider Types ----

# Provider-related types
ProviderType = str
ProviderName = str
ProviderConfig = Dict[str, Any]
ProviderCapabilities = Dict[str, Any]

# Common model types
ModelName = str
ModelConfig = Dict[str, Any]

# ---- Data Types ----


class DataType(str, Enum):
    """Types of data that can be processed by PepperPy.

    These types represent the fundamental data types that are used throughout
    the PepperPy framework.
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    EMBEDDING = "embedding"
    METADATA = "metadata"
    JSON = "json"
    BINARY = "binary"
    UNKNOWN = "unknown"


def get_data_type(value: Any) -> DataType:
    """Determine the data type of a value.

    Args:
        value: The value to determine the data type of

    Returns:
        The data type of the value
    """
    if value is None:
        return DataType.UNKNOWN

    if isinstance(value, str):
        return DataType.TEXT

    if isinstance(value, (bytes, bytearray)):
        return DataType.BINARY

    if isinstance(value, dict):
        return DataType.JSON

    if isinstance(value, (list, tuple)) and all(isinstance(x, float) for x in value):
        return DataType.EMBEDDING

    if isinstance(value, (list, tuple)):
        return DataType.JSON

    return DataType.UNKNOWN


# ---- Core Protocols ----


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


# ---- Type Inspection Utilities ----


def is_optional_type(type_: Type) -> bool:
    """Check if a type is Optional[T].

    Args:
        type_: The type to check

    Returns:
        True if the type is Optional[T], False otherwise
    """
    origin = get_origin(type_)
    if origin is Union:
        args = get_args(type_)
        return len(args) == 2 and type(None) in args
    return False


def get_optional_type(type_: Type) -> Optional[Type[Any]]:
    """Get the type T from Optional[T].

    Args:
        type_: The Optional[T] type

    Returns:
        The type T, or None if the type is not Optional[T]
    """
    if not is_optional_type(type_):
        return None
    args = get_args(type_)
    for arg in args:
        if arg is not type(None):
            return cast(Type[Any], arg)
    return None


def is_list_type(type_: Type) -> bool:
    """Check if a type is List[T].

    Args:
        type_: The type to check

    Returns:
        True if the type is List[T], False otherwise
    """
    origin = get_origin(type_)
    return origin is list


def get_list_type(type_: Type) -> Optional[Type[Any]]:
    """Get the type T from List[T].

    Args:
        type_: The List[T] type

    Returns:
        The type T, or None if the type is not List[T]
    """
    if not is_list_type(type_):
        return None
    args = get_args(type_)
    return cast(Type[Any], args[0]) if args else cast(Type[Any], Any)


def is_dict_type(type_: Type) -> bool:
    """Check if a type is Dict[K, V].

    Args:
        type_: The type to check

    Returns:
        True if the type is Dict[K, V], False otherwise
    """
    origin = get_origin(type_)
    return origin is dict


def get_dict_types(type_: Type) -> Optional[Tuple[Type[Any], Type[Any]]]:
    """Get the types K and V from Dict[K, V].

    Args:
        type_: The Dict[K, V] type

    Returns:
        A tuple of (K, V), or None if the type is not Dict[K, V]
    """
    if not is_dict_type(type_):
        return None
    args = get_args(type_)
    if len(args) == 2:
        return cast(Tuple[Type[Any], Type[Any]], args)
    return cast(Tuple[Type[Any], Type[Any]], (Any, Any))


def is_union_type(type_: Type) -> bool:
    """Check if a type is Union[...].

    Args:
        type_: The type to check

    Returns:
        True if the type is Union[...], False otherwise
    """
    origin = get_origin(type_)
    return origin is Union


def get_union_types(type_: Type) -> Optional[Tuple[Type, ...]]:
    """Get the types from Union[...].

    Args:
        type_: The Union[...] type

    Returns:
        A tuple of types, or None if the type is not Union[...]
    """
    if not is_union_type(type_):
        return None
    return get_args(type_)


def is_generic_type(type_: Type) -> bool:
    """Check if a type is a generic type.

    Args:
        type_: The type to check

    Returns:
        True if the type is a generic type, False otherwise
    """
    origin = get_origin(type_)
    return origin is not None


def get_generic_origin(type_: Type) -> Optional[Type]:
    """Get the origin of a generic type.

    Args:
        type_: The generic type

    Returns:
        The origin of the generic type, or None if the type is not generic
    """
    if not is_generic_type(type_):
        return None
    return get_origin(type_)


def get_generic_args(type_: Type) -> Optional[Tuple[Type, ...]]:
    """Get the type arguments of a generic type.

    Args:
        type_: The generic type

    Returns:
        A tuple of type arguments, or None if the type is not generic
    """
    if not is_generic_type(type_):
        return None
    return get_args(type_)


# ---- Class Inspection Utilities ----


class ClassInfo:
    """Information about a class.

    This class provides information about a class, including its methods and properties.
    """

    def __init__(self, cls: Type):
        """Initialize the class info.

        Args:
            cls: The class to get information about
        """
        self.cls = cls
        self.name = cls.__name__
        self.module = cls.__module__
        self.doc = cls.__doc__ or ""
        self.is_dataclass = is_dataclass(cls)
        self.methods = self._get_methods()
        self.properties = self._get_properties()

    def _get_methods(self) -> Mapping[str, Callable[..., Any]]:
        """Get the methods of the class.

        Returns:
            A dictionary mapping method names to method objects
        """
        methods: Dict[str, Callable[..., Any]] = {}
        for name, member in inspect.getmembers(self.cls, inspect.isfunction):
            if not name.startswith("_") or name == "__init__":
                methods[name] = member
        return methods

    def _get_properties(self) -> Dict[str, property]:
        """Get the properties of the class.

        Returns:
            A dictionary mapping property names to property objects
        """
        properties = {}
        for name, member in inspect.getmembers(
            self.cls, lambda x: isinstance(x, property)
        ):
            if not name.startswith("_"):
                properties[name] = member
        return properties

    def get_method_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a method.

        Args:
            name: The name of the method

        Returns:
            Information about the method, or None if the method is not found
        """
        method = self.methods.get(name)
        if method is None:
            return None

        signature = inspect.signature(method)
        doc = method.__doc__ or ""
        type_hints = get_type_hints(method)

        return {
            "name": name,
            "signature": str(signature),
            "doc": doc,
            "parameters": {
                param_name: {
                    "annotation": param.annotation,
                    "default": param.default
                    if param.default is not inspect.Parameter.empty
                    else None,
                    "kind": str(param.kind),
                }
                for param_name, param in signature.parameters.items()
            },
            "return_type": type_hints.get("return", Any),
        }

    def get_property_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a property.

        Args:
            name: The name of the property

        Returns:
            Information about the property, or None if the property is not found
        """
        prop = self.properties.get(name)
        if prop is None:
            return None

        doc = prop.__doc__ or ""
        type_hints = {}

        if prop.fget:
            type_hints = get_type_hints(prop.fget)

        return {
            "name": name,
            "doc": doc,
            "type": type_hints.get("return", Any),
            "readable": prop.fget is not None,
            "writable": prop.fset is not None,
            "deletable": prop.fdel is not None,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the class info to a dictionary.

        Returns:
            The class info as a dictionary
        """
        return {
            "name": self.name,
            "module": self.module,
            "doc": self.doc,
            "is_dataclass": self.is_dataclass,
            "methods": list(self.methods.keys()),
            "properties": list(self.properties.keys()),
        }


def get_class_info(cls: Type) -> ClassInfo:
    """Get information about a class.

    Args:
        cls: The class to get information about

    Returns:
        Information about the class
    """
    return ClassInfo(cls)


def get_module_classes(module: types.ModuleType) -> Dict[str, Type]:
    """Get the classes defined in a module.

    Args:
        module: The module to get classes from

    Returns:
        A dictionary mapping class names to class objects
    """
    return {
        name: member
        for name, member in inspect.getmembers(module, inspect.isclass)
        if member.__module__ == module.__name__
    }


# ---- Common Data Structures ----


@dataclass
class Metadata:
    """Consolidated metadata structure for documents and resources.

    Attributes:
        source: The source of the document or resource
        created_at: The creation time
        updated_at: The last update time
        author: The author
        title: The title
        tags: Tags for categorization
        custom: Custom metadata for extensibility
    """

    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metadata to a dictionary.

        Returns:
            The metadata as a dictionary
        """
        return {
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "title": self.title,
            "tags": list(self.tags),
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create metadata from a dictionary.

        Args:
            data: The dictionary to create the metadata from

        Returns:
            The created metadata
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None

        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                updated_at = None

        return cls(
            source=data.get("source"),
            created_at=created_at,
            updated_at=updated_at,
            author=data.get("author"),
            title=data.get("title"),
            tags=set(data.get("tags", [])),
            custom=data.get("custom", {}),
        )


@dataclass
class Document:
    """Consolidated document structure.

    Attributes:
        content: The content of the document
        metadata: Metadata for the document
        id: The ID of the document
    """

    content: str
    metadata: Metadata = field(default_factory=Metadata)
    id: str = field(default="")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document to a dictionary.

        Returns:
            The document as a dictionary
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a document from a dictionary.

        Args:
            data: The dictionary to create the document from

        Returns:
            The created document
        """
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=Metadata.from_dict(data.get("metadata", {})),
        )


@dataclass
class Result(Generic[T]):
    """Consolidated result structure for operation results.

    Attributes:
        success: Whether the operation was successful
        data: The data returned by the operation
        error: The error that occurred, if any
        metadata: Additional metadata for the result
    """

    success: bool = True
    data: Optional[T] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            The result as a dictionary
        """
        return {
            "success": self.success,
            "data": self.data,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata,
        }


@dataclass
class Context:
    """Consolidated context structure for operations.

    Attributes:
        data: The context data
        metadata: Metadata for the context
    """

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context.

        Args:
            key: The key to get
            default: The default value if the key is not found

        Returns:
            The value for the key, or the default if not found
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context.

        Args:
            key: The key to set
            value: The value to set
        """
        self.data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a dictionary.

        Returns:
            The context as a dictionary
        """
        return {
            "data": self.data,
            "metadata": self.metadata,
        }


@dataclass
class VectorEmbedding:
    """A vector embedding for a document chunk.

    Attributes:
        vector: The vector embedding
        document_id: The ID of the document this embedding belongs to
        chunk_id: The ID of the document chunk this embedding belongs to
        metadata: Additional metadata for the embedding
    """

    vector: List[float]
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the vector embedding to a dictionary.

        Returns:
            The vector embedding as a dictionary
        """
        return {
            "vector": self.vector,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorEmbedding":
        """Create a vector embedding from a dictionary.

        Args:
            data: The dictionary to create the vector embedding from

        Returns:
            The created vector embedding
        """
        return cls(
            vector=data.get("vector", []),
            document_id=data.get("document_id", ""),
            chunk_id=data.get("chunk_id", ""),
            metadata=data.get("metadata", {}),
        )
