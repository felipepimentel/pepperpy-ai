"""Core Base Module.

This module defines the core interfaces, types and errors used throughout
the PepperPy framework. It provides the foundation for all other modules.

Example:
    >>> from pepperpy.core.base import BaseProvider
    >>> class MyProvider(BaseProvider):
    ...     def __init__(self, name: str, **kwargs):
    ...         super().__init__(name, **kwargs)
    ...         self.provider_type = "custom"
"""

from abc import ABC
from typing import Any, Dict, Optional, Protocol, TypeVar, Union

# Type definitions
ConfigType = Dict[str, Any]
HeadersType = Dict[str, str]
QueryParamsType = Union[Dict[str, Any], str]
JsonType = Any


# Base Exceptions
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

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Error message
        """
        return self.message


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


# Provider Interfaces
T = TypeVar("T", bound="BaseProvider")


class BaseProvider(Protocol):
    """Base protocol for all providers.

    All providers in PepperPy must implement this protocol to ensure consistent
    behavior across different implementations.
    """

    name: str

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider to set up any
        necessary resources or connections.
        """
        ...

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        ...


class RemoteProvider(BaseProvider):
    """Base class for remote providers.

    This class extends BaseProvider with functionality specific to
    remote services, such as base URL management and API versioning.

    Args:
        name: Provider name
        base_url: Base URL for API calls
        config: Optional configuration dictionary
        **kwargs: Additional provider-specific configuration
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        config: Optional[ConfigType] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the remote provider.

        Args:
            name: Provider name
            base_url: Base URL for API calls
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self.provider_type = "remote"
        self.base_url = base_url.rstrip("/")
        self._config = config or {}
        self._config.update(kwargs)

    def get_endpoint(self, path: str) -> str:
        """Get full endpoint URL.

        Args:
            path: Endpoint path

        Returns:
            Full endpoint URL
        """
        return f"{self.base_url}/{path.lstrip('/')}"


class LocalProvider(BaseProvider):
    """Base class for local providers."""

    name = "local"


class RestProvider(RemoteProvider):
    """Base class for REST API providers."""

    name = "rest"

    async def get(self, path: str, **kwargs: Any) -> Any:
        """Send GET request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError

    async def post(self, path: str, **kwargs: Any) -> Any:
        """Send POST request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError

    async def put(self, path: str, **kwargs: Any) -> Any:
        """Send PUT request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError

    async def delete(self, path: str, **kwargs: Any) -> Any:
        """Send DELETE request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError


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


"""Base classes and interfaces for PepperPy."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T", bound="BaseComponent")


class BaseComponent(ABC):
    """Base class for all PepperPy components."""

    def __init__(self) -> None:
        """Initialize the component."""
        self._initialized = False
        self._options: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the component."""
        if not self._initialized:
            await self._initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._initialized:
            await self._cleanup()
            self._initialized = False

    async def _initialize(self) -> None:
        """Initialize implementation."""
        pass

    async def _cleanup(self) -> None:
        """Cleanup implementation."""
        pass

    async def __aenter__(self) -> "BaseComponent":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.cleanup()

    def configure(self: T, **options: Any) -> T:
        """Configure the component.

        Args:
            **options: Configuration options

        Returns:
            Self for chaining
        """
        self._options.update(options)
        return self


class BaseBuilder(ABC):
    """Base class for builders."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self._options: Dict[str, Any] = {}

    def configure(self: T, **options: Any) -> T:
        """Configure the builder.

        Args:
            **options: Configuration options

        Returns:
            Self for chaining
        """
        self._options.update(options)
        return self

    @abstractmethod
    def build(self) -> Any:
        """Build the component.

        Returns:
            Built component
        """
        pass


class PepperPy:
    """Main entry point for PepperPy framework."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize PepperPy.

        Args:
            config_path: Optional path to configuration file
        """
        from pepperpy.core import Config

        self.config = Config(config_path=config_path)
        self._components: Dict[str, BaseComponent] = {}

    @classmethod
    def create(cls, config_path: Optional[str] = None) -> "PepperPy":
        """Create a new PepperPy instance.

        Args:
            config_path: Optional path to configuration file

        Returns:
            New PepperPy instance
        """
        return cls(config_path=config_path)

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        for component in self._components.values():
            await component.cleanup()

    @property
    def llm(self) -> "LLMComponent":
        """Get LLM component."""
        from pepperpy.llm import LLMComponent

        if "llm" not in self._components:
            self._components["llm"] = LLMComponent(self.config)
        return self._components["llm"]

    @property
    def embeddings(self) -> "EmbeddingComponent":
        """Get embeddings component."""
        from pepperpy.embeddings import EmbeddingComponent

        if "embeddings" not in self._components:
            self._components["embeddings"] = EmbeddingComponent(self.config)
        return self._components["embeddings"]

    @property
    def rag(self) -> "RAGComponent":
        """Get RAG component."""
        from pepperpy.rag import RAGComponent

        if "rag" not in self._components:
            self._components["rag"] = RAGComponent(self.config)
        return self._components["rag"]

    @property
    def github(self) -> "GitHubComponent":
        """Get GitHub component."""
        from pepperpy.github import GitHubComponent

        if "github" not in self._components:
            self._components["github"] = GitHubComponent(self.config)
        return self._components["github"]

    def create_assistant(self, name: Optional[str] = None) -> "AssistantBuilder":
        """Create a new assistant builder.

        Args:
            name: Optional assistant name

        Returns:
            Assistant builder
        """
        from pepperpy.assistants import AssistantBuilder

        return AssistantBuilder(self, name)
