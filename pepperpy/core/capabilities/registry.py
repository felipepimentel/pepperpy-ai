"""Registry for managing capabilities.

This module provides a simplified registry for managing capabilities in the
Pepperpy framework.
"""

from typing import Dict, List, Optional, Type
from uuid import UUID, uuid4

from pepperpy.core.errors import RegistryError
from pepperpy.monitoring import logger

from .base import Capability, CapabilityConfig


class CapabilityRegistry:
    """Registry for managing capabilities.

    This class provides a simplified interface for registering and managing
    capabilities in the system.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._capabilities: Dict[str, Dict[str, Type[Capability]]] = {}
        self._instances: Dict[UUID, Capability] = {}
        self._configs: Dict[UUID, CapabilityConfig] = {}

    def register(
        self,
        capability_class: Type[Capability],
        config: CapabilityConfig,
    ) -> UUID:
        """Register a capability.

        Args:
            capability_class: Capability class to register
            config: Configuration for the capability

        Returns:
            UUID of the registered capability

        Raises:
            ValueError: If capability is invalid
            RegistryError: If registration fails

        """
        try:
            # Validate capability class
            if not hasattr(capability_class, "name"):
                raise ValueError("Capability class must have a name attribute")

            # Create capability instance with config
            capability = capability_class(**config.model_dump())

            # Generate ID and store
            capability_id = uuid4()
            self._instances[capability_id] = capability
            self._configs[capability_id] = config

            # Store in capability map
            if config.name not in self._capabilities:
                self._capabilities[config.name] = {}
            self._capabilities[config.name][config.version] = capability_class

            logger.info(
                "Registered capability",
                extra={
                    "capability_name": config.name,
                    "capability_version": config.version,
                    "capability_id": str(capability_id),
                },
            )

            return capability_id

        except Exception as e:
            raise RegistryError(f"Failed to register capability: {e}") from e

    def unregister(self, capability_id: UUID) -> None:
        """Unregister a capability.

        Args:
            capability_id: ID of capability to unregister

        Raises:
            KeyError: If capability not found

        """
        if capability_id not in self._instances:
            raise KeyError(f"Capability {capability_id} not found")

        capability = self._instances[capability_id]
        config = self._configs[capability_id]

        # Remove from maps
        del self._instances[capability_id]
        del self._configs[capability_id]

        # Remove from capability map if no more versions
        versions = self._capabilities.get(config.name, {})
        if config.version in versions:
            del versions[config.version]
            if not versions:
                del self._capabilities[config.name]

        logger.info(
            "Unregistered capability",
            extra={
                "capability_name": config.name,
                "capability_version": config.version,
                "capability_id": str(capability_id),
            },
        )

    def get(self, capability_id: UUID) -> Optional[Capability]:
        """Get a capability by ID.

        Args:
            capability_id: ID of capability to get

        Returns:
            Capability instance if found, None otherwise

        """
        return self._instances.get(capability_id)

    def get_config(self, capability_id: UUID) -> Optional[CapabilityConfig]:
        """Get capability configuration.

        Args:
            capability_id: ID of capability to get config for

        Returns:
            Capability configuration if found, None otherwise

        """
        return self._configs.get(capability_id)

    def list_capabilities(self) -> List[CapabilityConfig]:
        """List all registered capabilities.

        Returns:
            List of capability configurations

        """
        return list(self._configs.values())

    def get_by_name(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[Type[Capability]]:
        """Get capability class by name and version.

        Args:
            name: Capability name
            version: Optional specific version

        Returns:
            Capability class if found, None otherwise

        """
        versions = self._capabilities.get(name, {})
        if not versions:
            return None

        if version:
            return versions.get(version)

        # Return latest version if no specific version requested
        latest = max(versions.keys())
        return versions[latest]

    def clear(self) -> None:
        """Clear all registered capabilities."""
        self._capabilities.clear()
        self._instances.clear()
        self._configs.clear()
        logger.info("Cleared capability registry")
