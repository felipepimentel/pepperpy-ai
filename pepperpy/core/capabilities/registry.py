"""Registry for managing capabilities.

This module provides a simplified registry for managing capabilities in the
Pepperpy framework.
"""

from typing import Dict, List, Optional, Type
from uuid import UUID, uuid4

from loguru import logger

from pepperpy.core.errors import RegistryError

from .base import Capability, CapabilityContext
from .errors import CapabilityType


class CapabilityRegistry:
    """Registry for managing capabilities.

    This class provides a simplified interface for registering and managing
    capabilities in the system.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._capabilities: Dict[str, Dict[str, Type[Capability]]] = {}
        self._instances: Dict[UUID, Capability] = {}
        self._contexts: Dict[UUID, CapabilityContext] = {}

    def register(
        self,
        capability_class: Type[Capability],
        capability_type: CapabilityType,
        metadata: Dict[str, str],
        config: Optional[Dict[str, str]] = None,
    ) -> UUID:
        """Register a capability.

        Args:
            capability_class: Capability class to register
            capability_type: Type of capability
            metadata: Metadata for the capability
            config: Optional configuration for the capability

        Returns:
            UUID of the registered capability

        Raises:
            ValueError: If capability is invalid
            RegistryError: If registration fails

        """
        try:
            # Create capability instance with context
            context = CapabilityContext(
                capability_type=capability_type,
                metadata=metadata,
                config=config,
            )
            capability = capability_class(capability_type)

            # Generate ID and store
            capability_id = uuid4()
            self._instances[capability_id] = capability
            self._contexts[capability_id] = context

            # Store in capability map
            if capability_type.value not in self._capabilities:
                self._capabilities[capability_type.value] = {}
            self._capabilities[capability_type.value][str(capability_id)] = (
                capability_class
            )

            logger.info(
                "Registered capability",
                extra={
                    "capability_type": capability_type.value,
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
        context = self._contexts[capability_id]

        # Remove from maps
        del self._instances[capability_id]
        del self._contexts[capability_id]

        # Remove from capability map if no more instances
        instances = self._capabilities.get(context.capability_type.value, {})
        if str(capability_id) in instances:
            del instances[str(capability_id)]
            if not instances:
                del self._capabilities[context.capability_type.value]

        logger.info(
            "Unregistered capability",
            extra={
                "capability_type": context.capability_type.value,
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

    def get_context(self, capability_id: UUID) -> Optional[CapabilityContext]:
        """Get capability context.

        Args:
            capability_id: ID of capability to get context for

        Returns:
            Capability context if found, None otherwise

        """
        return self._contexts.get(capability_id)

    def list_capabilities(self) -> List[CapabilityContext]:
        """List all registered capabilities.

        Returns:
            List of capability contexts

        """
        return list(self._contexts.values())

    def get_by_type(
        self,
        capability_type: CapabilityType,
    ) -> List[UUID]:
        """Get capability IDs by type.

        Args:
            capability_type: Type of capabilities to get

        Returns:
            List of capability IDs of the specified type

        """
        instances = self._capabilities.get(capability_type.value, {})
        return [UUID(id_str) for id_str in instances.keys()]

    def clear(self) -> None:
        """Clear all registered capabilities."""
        self._capabilities.clear()
        self._instances.clear()
        self._contexts.clear()
        logger.info("Cleared capability registry")
