"""Registry for capabilities.

This module provides a registry for capabilities that can be used by agents
and other components.
"""

from typing import Dict, Optional, Type

from pepperpy.capabilities.base import BaseCapability


class CapabilityRegistry:
    """Registry for capabilities."""

    _capabilities: Dict[str, Type[BaseCapability]] = {}

    @classmethod
    def register(
        cls, capability_type: str, capability_class: Type[BaseCapability]
    ) -> None:
        """Register a capability.

        Args:
            capability_type: Capability type identifier
            capability_class: Capability class
        """
        cls._capabilities[capability_type] = capability_class

    @classmethod
    def get(cls, capability_type: str) -> Optional[Type[BaseCapability]]:
        """Get a capability by type.

        Args:
            capability_type: Capability type identifier

        Returns:
            Capability class or None if not found
        """
        return cls._capabilities.get(capability_type)

    @classmethod
    def list_capabilities(cls) -> Dict[str, Type[BaseCapability]]:
        """List all registered capabilities.

        Returns:
            Dictionary mapping capability types to capability classes
        """
        return cls._capabilities.copy()
