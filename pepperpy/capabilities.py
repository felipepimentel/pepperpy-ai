"""PepperPy Capabilities Module.

This module provides components for managing capabilities in the PepperPy framework, including:
- Capability registration and discovery
- Capability metadata management
- Provider capability checking

The capabilities module is used to define and manage the features and
functionalities that providers can support.
"""

from typing import Any, Dict, List, Optional, Set

from pepperpy.core.errors import PepperPyError


class CapabilityError(PepperPyError):
    """Error raised when a capability operation fails."""

    pass


class Capability:
    """Represents a capability that can be provided by a provider."""

    def __init__(self, name: str, description: str):
        """Initialize a capability.

        Args:
            name: The name of the capability
            description: A description of the capability
        """
        self.name = name
        self.description = description

    def __eq__(self, other: Any) -> bool:
        """Check if two capabilities are equal.

        Args:
            other: The other capability to compare with

        Returns:
            True if the capabilities are equal, False otherwise
        """
        if not isinstance(other, Capability):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """Get the hash of the capability.

        Returns:
            The hash of the capability
        """
        return hash(self.name)


class CapabilityRegistry:
    """Registry for capabilities."""

    def __init__(self):
        """Initialize the registry."""
        self._capabilities: Dict[str, Capability] = {}
        self._provider_capabilities: Dict[str, Set[str]] = {}

    def register_capability(self, capability: Capability) -> None:
        """Register a capability.

        Args:
            capability: The capability to register

        Raises:
            CapabilityError: If the capability is already registered
        """
        if capability.name in self._capabilities:
            raise CapabilityError(f"Capability {capability.name} already registered")
        self._capabilities[capability.name] = capability

    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability by name.

        Args:
            name: The name of the capability

        Returns:
            The capability, or None if not found
        """
        return self._capabilities.get(name)

    def list_capabilities(self) -> List[Capability]:
        """List all registered capabilities.

        Returns:
            A list of all registered capabilities
        """
        return list(self._capabilities.values())

    def register_provider_capability(
        self, provider_id: str, capability_name: str
    ) -> None:
        """Register a capability for a provider.

        Args:
            provider_id: The ID of the provider
            capability_name: The name of the capability

        Raises:
            CapabilityError: If the capability is not registered
        """
        if capability_name not in self._capabilities:
            raise CapabilityError(f"Capability {capability_name} not registered")

        if provider_id not in self._provider_capabilities:
            self._provider_capabilities[provider_id] = set()

        self._provider_capabilities[provider_id].add(capability_name)

    def provider_has_capability(self, provider_id: str, capability_name: str) -> bool:
        """Check if a provider has a capability.

        Args:
            provider_id: The ID of the provider
            capability_name: The name of the capability

        Returns:
            True if the provider has the capability, False otherwise
        """
        if provider_id not in self._provider_capabilities:
            return False
        return capability_name in self._provider_capabilities[provider_id]

    def get_provider_capabilities(self, provider_id: str) -> List[Capability]:
        """Get all capabilities of a provider.

        Args:
            provider_id: The ID of the provider

        Returns:
            A list of all capabilities of the provider
        """
        if provider_id not in self._provider_capabilities:
            return []

        return [
            self._capabilities[name]
            for name in self._provider_capabilities[provider_id]
            if name in self._capabilities
        ]


# Global registry instance
_registry = CapabilityRegistry()


def register_capability(name: str, description: str) -> Capability:
    """Register a new capability.

    Args:
        name: The name of the capability
        description: A description of the capability

    Returns:
        The registered capability

    Raises:
        CapabilityError: If the capability is already registered
    """
    capability = Capability(name, description)
    _registry.register_capability(capability)
    return capability


def get_capability(name: str) -> Optional[Capability]:
    """Get a capability by name.

    Args:
        name: The name of the capability

    Returns:
        The capability, or None if not found
    """
    return _registry.get_capability(name)


def list_capabilities() -> List[Capability]:
    """List all registered capabilities.

    Returns:
        A list of all registered capabilities
    """
    return _registry.list_capabilities()


def register_provider_capability(provider_id: str, capability_name: str) -> None:
    """Register a capability for a provider.

    Args:
        provider_id: The ID of the provider
        capability_name: The name of the capability

    Raises:
        CapabilityError: If the capability is not registered
    """
    _registry.register_provider_capability(provider_id, capability_name)


def provider_has_capability(provider_id: str, capability_name: str) -> bool:
    """Check if a provider has a capability.

    Args:
        provider_id: The ID of the provider
        capability_name: The name of the capability

    Returns:
        True if the provider has the capability, False otherwise
    """
    return _registry.provider_has_capability(provider_id, capability_name)


def get_provider_capabilities(provider_id: str) -> List[Capability]:
    """Get all capabilities of a provider.

    Args:
        provider_id: The ID of the provider

    Returns:
        A list of all capabilities of the provider
    """
    return _registry.get_provider_capabilities(provider_id)


__all__ = [
    "Capability",
    "CapabilityError",
    "CapabilityRegistry",
    "register_capability",
    "get_capability",
    "list_capabilities",
    "register_provider_capability",
    "provider_has_capability",
    "get_provider_capabilities",
]
