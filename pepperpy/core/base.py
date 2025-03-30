"""Core Base Module.

This module defines the core interfaces, types, errors and factories used throughout
the PepperPy framework. It provides the foundation for all other modules.

Example:
    >>> from pepperpy.core.base import BaseProvider
    >>> class MyProvider(BaseProvider):
    ...     def __init__(self, name: str, **kwargs):
    ...         super().__init__(name, **kwargs)
    ...         self.provider_type = "custom"
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)

T = TypeVar("T")
P = TypeVar("P", bound="BaseProvider")


# Common Types
Metadata = Dict[str, Any]
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], list]
JsonDict = Dict[str, JsonValue]
JsonType = Union[Dict[str, Any], List[Any]]

# Provider Types
ConfigType = Dict[str, Any]
HeadersType = Dict[str, str]
QueryParamsType = Union[Dict[str, Any], str]

# Message types
MessageType = Dict[str, Any]
MessageListType = List[MessageType]

# Response types
ResponseType = Dict[str, Any]
ResponseListType = List[ResponseType]

# Error types
ErrorType = Dict[str, Any]
ErrorListType = List[ErrorType]

# Metadata types
MetadataType = Dict[str, Any]
MetadataListType = List[MetadataType]

# Component types
ComponentType = str
ComponentConfigType = Dict[str, Any]

# Pipeline types
PipelineType = str
PipelineConfigType = Dict[str, Any]

# Workflow types
WorkflowType = str
WorkflowConfigType = Dict[str, Any]

# Document types
DocumentType = str
DocumentConfigType = Dict[str, Any]

# Memory types
MemoryType = str
MemoryConfigType = Dict[str, Any]

# Storage types
StorageType = str
StorageConfigType = Dict[str, Any]

# Embedding types
EmbeddingType = List[float]
EmbeddingListType = List[EmbeddingType]

# Token types
TokenType = str
TokenListType = List[TokenType]

# Function types
FunctionType = str
FunctionConfigType = Dict[str, Any]

# Tool types
ToolType = str
ToolConfigType = Dict[str, Any]

# Agent types
AgentType = str
AgentConfigType = Dict[str, Any]

# Task types
TaskType = str
TaskConfigType = Dict[str, Any]

# Event types
EventType = str
EventConfigType = Dict[str, Any]

# State types
StateType = str
StateConfigType = Dict[str, Any]

# Context types
ContextType = str
ContextConfigType = Dict[str, Any]

# Result types
ResultType = Dict[str, Any]
ResultListType = List[ResultType]


# Core Exceptions
class PepperpyError(Exception):
    """Base class for all PepperPy exceptions."""

    def __init__(self, message: str, *args, **kwargs):
        """Initialize a PepperPy error.

        Args:
            message: Error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)


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


class BaseProvider(ABC):
    """Base class for all providers."""

    def __init__(
        self,
        name: str = "base",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self._config = config or {}
        self._config.update(kwargs)
        self.initialized = False

    @property
    def config(self) -> Dict[str, Any]:
        """Get provider configuration.

        Returns:
            Configuration dictionary
        """
        return self._config

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        It can be used to set up any necessary resources or connections.
        """
        if not self.initialized:
            await self._initialize()
            self.initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        It can be used to clean up any resources or connections.
        """
        if self.initialized:
            await self._cleanup()
            self.initialized = False

    async def _initialize(self) -> None:
        """Initialize implementation."""
        pass

    async def _cleanup(self) -> None:
        """Cleanup implementation."""
        pass

    async def __aenter__(self) -> "BaseProvider":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.cleanup()

    def configure(self, **options: Any) -> "BaseProvider":
        """Configure the provider.

        Args:
            **options: Configuration options

        Returns:
            Self for chaining
        """
        self._config.update(options)
        return self


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


# Core Exceptions
class ProviderError(PepperpyError):
    """Error raised by providers during initialization or execution."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.provider = provider
        self.operation = operation

    def __str__(self) -> str:
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        return " | ".join(parts)


class ValidationError(PepperpyError):
    """Error raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        rule: Optional[str] = None,
        value: Optional[Any] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.field = field
        self.rule = rule
        self.value = value

    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.rule:
            parts.append(f"Rule: {self.rule}")
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        return " | ".join(parts)


class ConfigurationError(PepperpyError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.config_key = config_key
        self.config_value = config_value

    def __str__(self) -> str:
        parts = [self.message]
        if self.config_key:
            parts.append(f"Key: {self.config_key}")
        if self.config_value is not None:
            parts.append(f"Value: {self.config_value}")
        return " | ".join(parts)


class HTTPError(PepperpyError):
    """Base class for HTTP errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RequestError(HTTPError):
    """Error during HTTP request preparation."""

    def __init__(self, message: str, request_info: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.request_info = request_info or {}


class ResponseError(HTTPError):
    """Error processing HTTP response."""

    def __init__(self, message: str, response_info: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.response_info = response_info or {}


class ConnectionError(HTTPError):
    """Error connecting to HTTP server."""

    def __init__(self, message: str, host: Optional[str] = None):
        super().__init__(message)
        self.host = host


class TimeoutError(HTTPError):
    """Error when HTTP request times out."""

    def __init__(self, message: str, timeout: Optional[float] = None):
        super().__init__(message)
        self.timeout = timeout


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


# Provider Interfaces
class LLMProvider(BaseProvider):
    """Base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a chat response."""
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationResult]:
        """Stream a chat response."""
        ...


class RAGProvider(BaseProvider):
    """Base class for RAG providers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search for relevant documents."""
        ...

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the RAG system."""
        ...


class StorageProvider(BaseProvider):
    """Base class for storage providers."""

    @abstractmethod
    async def load_document(
        self,
        path: str,
        **kwargs: Any,
    ) -> Document:
        """Load a document from storage."""
        ...

    @abstractmethod
    async def save_document(
        self,
        document: Document,
        path: str,
        **kwargs: Any,
    ) -> None:
        """Save a document to storage."""
        ...


class WorkflowProvider(BaseProvider):
    """Base class for workflow providers."""

    @abstractmethod
    async def execute(
        self,
        workflow: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        ...

    @abstractmethod
    async def get_status(
        self,
        workflow_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Get workflow status."""
        ...


# Factory Functions
def create_provider(
    provider_type: str,
    provider_map: Dict[str, Type[P]],
    config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> P:
    """Create a provider instance.

    Args:
        provider_type: Type of provider to create
        provider_map: Mapping of provider types to classes
        config: Optional configuration dictionary
        **kwargs: Additional provider-specific configuration

    Returns:
        Provider instance

    Raises:
        ConfigurationError: If provider type is invalid
    """
    if provider_type not in provider_map:
        raise ConfigurationError(
            f"Invalid provider type: {provider_type}. "
            f"Valid types: {', '.join(provider_map.keys())}"
        )

    provider_class = provider_map[provider_type]
    return provider_class(config=config, **kwargs)


# Exports
__all__ = [
    # Types
    "Metadata",
    "JsonValue",
    "JsonDict",
    "JsonType",
    "ConfigType",
    "HeadersType",
    "QueryParamsType",
    # Results
    "GenerationResult",
    "SearchResult",
    "Document",
    # Errors
    "PepperpyError",
    "ProviderError",
    "ValidationError",
    "ConfigurationError",
    "HTTPError",
    "RequestError",
    "ResponseError",
    "ConnectionError",
    "TimeoutError",
    # Protocols and Base Classes
    "ModelContext",
    "BaseModelContext",
    "BaseProvider",
    # Provider Interfaces
    "LLMProvider",
    "RAGProvider",
    "StorageProvider",
    "WorkflowProvider",
    # Factory Functions
    "create_provider",
]
