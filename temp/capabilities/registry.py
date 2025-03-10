"""Registry for capabilities in PepperPy.

This module provides a registry for capabilities in the PepperPy framework.
Capabilities represent features or functionalities that providers can support.
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.interfaces import ProviderCapability


class CapabilityRegistry:
    """Registry for capabilities.

    The capability registry keeps track of available capabilities and their
    descriptions.
    """

    def __init__(self):
        """Initialize the capability registry."""
        self._capabilities: Dict[str, ProviderCapability] = {}

    def register(self, capability: ProviderCapability) -> None:
        """Register a capability.

        Args:
            capability: The capability to register

        Raises:
            ValueError: If a capability with the same name is already registered
        """
        if capability.name in self._capabilities:
            raise ValueError(f"Capability '{capability.name}' is already registered")
        self._capabilities[capability.name] = capability

    def get(self, name: str) -> Optional[ProviderCapability]:
        """Get a capability by name.

        Args:
            name: The name of the capability

        Returns:
            The capability, or None if not found
        """
        return self._capabilities.get(name)

    def list_names(self) -> List[str]:
        """List all registered capability names.

        Returns:
            A list of registered capability names
        """
        return list(self._capabilities.keys())

    def list_capabilities(self) -> List[ProviderCapability]:
        """List all registered capabilities.

        Returns:
            A list of registered capabilities
        """
        return list(self._capabilities.values())

    def has_capability(self, name: str) -> bool:
        """Check if a capability is registered.

        Args:
            name: The name of the capability

        Returns:
            True if the capability is registered, False otherwise
        """
        return name in self._capabilities


# Global capability registry
capability_registry = CapabilityRegistry()


def register_capability(
    name: str, description: str, metadata: Optional[Dict[str, Any]] = None
) -> ProviderCapability:
    """Register a capability.

    Args:
        name: The name of the capability
        description: A description of the capability
        metadata: Additional metadata for the capability

    Returns:
        The registered capability

    Raises:
        ValueError: If a capability with the same name is already registered
    """
    capability = ProviderCapability(name, description, metadata)
    capability_registry.register(capability)
    return capability


def get_capability(name: str) -> Optional[ProviderCapability]:
    """Get a capability by name.

    Args:
        name: The name of the capability

    Returns:
        The capability, or None if not found
    """
    return capability_registry.get(name)


def list_capability_names() -> List[str]:
    """List all registered capability names.

    Returns:
        A list of registered capability names
    """
    return capability_registry.list_names()


def list_capabilities() -> List[ProviderCapability]:
    """List all registered capabilities.

    Returns:
        A list of registered capabilities
    """
    return capability_registry.list_capabilities()


def has_capability(name: str) -> bool:
    """Check if a capability is registered.

    Args:
        name: The name of the capability

    Returns:
        True if the capability is registered, False otherwise
    """
    return capability_registry.has_capability(name)
