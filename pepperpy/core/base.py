"""Provider Base Module.

This module defines the base provider interface and common functionality
for all provider implementations across the framework.

Example:
    >>> from pepperpy.core.provider import BaseProvider
    >>> class MyProvider(BaseProvider):
    ...     def __init__(self, name: str, **kwargs):
    ...         super().__init__(name, **kwargs)
    ...         self.provider_type = "custom"
"""

from typing import Any, Dict, TypeVar

from .validation import ValidationError

T = TypeVar("T", bound="BaseProvider")


class BaseProvider:
    """Base class for all providers.

    This class defines the common interface and functionality that all
    providers must implement. It provides basic provider lifecycle
    management and capability introspection.

    Args:
        name: Provider name
        **kwargs: Provider-specific configuration

    Example:
        >>> class MyProvider(BaseProvider):
        ...     def __init__(self, name: str, **kwargs):
        ...         super().__init__(name, **kwargs)
        ...         self.provider_type = "custom"
        ...
        >>> provider = MyProvider("my_provider")
    """

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the provider.

        Args:
            name: Provider name
            **kwargs: Provider-specific configuration

        Raises:
            ValidationError: If name is empty
        """
        if not name:
            raise ValidationError("Provider name cannot be empty")

        self.name = name
        self.provider_type = "base"
        self._capabilities: Dict[str, Any] = {}
        self._config = kwargs

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dict with provider capabilities including:
                - name: Provider name
                - type: Provider type
                - capabilities: Provider-specific capabilities

        Example:
            >>> provider = MyProvider("my_provider")
            >>> caps = provider.get_capabilities()
            >>> print(caps["name"])
        """
        return {
            "name": self.name,
            "type": self.provider_type,
            "capabilities": self._capabilities,
        }

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            Provider name and type
        """
        return f"{self.name} ({self.provider_type})"

    def __repr__(self) -> str:
        """Get detailed string representation.

        Returns:
            Provider details including name, type and capabilities
        """
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"type='{self.provider_type}', "
            f"capabilities={self._capabilities})"
        )
