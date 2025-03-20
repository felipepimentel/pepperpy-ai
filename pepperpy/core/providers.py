"""Base provider implementations for PepperPy.

This module contains the core provider abstractions that are used throughout
the PepperPy framework. These providers define the fundamental interfaces
for different types of service implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T")


class BaseProvider(ABC):
    """Base class for all providers in PepperPy."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the provider configuration."""
        pass


class LocalProvider(BaseProvider):
    """Base class for local providers that run on the same machine."""

    def initialize(self) -> None:
        """Initialize local provider resources."""
        pass

    def validate(self) -> bool:
        """Validate local provider configuration."""
        return True


class RemoteProvider(BaseProvider):
    """Base class for remote providers that connect to external services."""

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a remote provider.

        Args:
            host: The host address of the remote service
            port: Optional port number
            credentials: Optional credentials for authentication
        """
        self.host = host
        self.port = port
        self.credentials = credentials or {}

    def initialize(self) -> None:
        """Initialize remote connection."""
        pass

    def validate(self) -> bool:
        """Validate remote connection configuration."""
        return bool(self.host)


class RestProvider(RemoteProvider):
    """Base class for REST API providers."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize a REST provider.

        Args:
            base_url: The base URL for the REST API
            api_key: Optional API key for authentication
            headers: Optional additional headers
        """
        super().__init__(host=base_url)
        self.base_url = base_url
        self.api_key = api_key
        self.headers = headers or {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def validate(self) -> bool:
        """Validate REST provider configuration."""
        return bool(self.base_url)
