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

import abc
from typing import Any, Dict, Optional, TypeVar, Union, Tuple, Protocol

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
        **kwargs
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
        **kwargs
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
        **kwargs
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
