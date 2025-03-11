"""Core functionality for capabilities in PepperPy.

This module provides the core functionality for capabilities in the PepperPy framework.
Capabilities represent features or functionalities that providers can support.
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.interfaces import ProviderCapability
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Global capability registry
_REGISTRY = None


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
        logger.debug(f"Registered capability: {capability.name}")

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


def _get_registry() -> CapabilityRegistry:
    """Get the global capability registry.

    Returns:
        The global capability registry
    """
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = CapabilityRegistry()
    return _REGISTRY


def register_capability(
    name: str, description: str, metadata: Optional[Dict[str, Any]] = None
) -> ProviderCapability:
    """Register a new capability.

    Args:
        name: The name of the capability
        description: A description of the capability
        metadata: Optional metadata for the capability

    Returns:
        The registered capability

    Raises:
        ValueError: If a capability with the same name is already registered
    """
    capability = ProviderCapability(
        name=name, description=description, metadata=metadata or {}
    )
    _get_registry().register(capability)
    logger.info(f"Registered capability: {name}")
    return capability


def get_capability(name: str) -> Optional[ProviderCapability]:
    """Get a capability by name.

    Args:
        name: The name of the capability

    Returns:
        The capability, or None if not found
    """
    return _get_registry().get(name)


def list_capability_names() -> List[str]:
    """List all registered capability names.

    Returns:
        A list of registered capability names
    """
    return _get_registry().list_names()


def list_capabilities() -> List[ProviderCapability]:
    """List all registered capabilities.

    Returns:
        A list of registered capabilities
    """
    return _get_registry().list_capabilities()


def has_capability(name: str) -> bool:
    """Check if a capability is registered.

    Args:
        name: The name of the capability

    Returns:
        True if the capability is registered, False otherwise
    """
    return _get_registry().has_capability(name)
