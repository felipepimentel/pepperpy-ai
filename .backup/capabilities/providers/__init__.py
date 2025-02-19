"""Capability provider interfaces.

This module provides the interfaces for capability providers, which are
responsible for creating and managing capabilities of specific types.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID, uuid4

from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger

from ..base import BaseCapability, CapabilityType
from ..base import CapabilityMetadata as CapabilityMetadata

logger = get_logger(__name__)


class CapabilityProvider(BaseComponent):
    """Base class for capability providers.

    Capability providers are responsible for creating and managing capabilities
    of specific types. They handle capability lifecycle and ensure proper
    cleanup.

    Attributes:
        id: Unique identifier
        metadata: Provider metadata
        capability_type: Type of capabilities this provider manages
        capabilities: Dictionary of managed capabilities

    Example:
        >>> provider = PromptProvider()
        >>> capability = await provider.create_capability(
        ...     name="gpt4_prompt",
        ...     config={"model": "gpt-4"}
        ... )
        >>> assert capability.state.is_ready()

    """

    def __init__(
        self,
        capability_type: CapabilityType,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the capability provider.

        Args:
            capability_type: Type of capabilities this provider manages
            id: Optional provider ID

        Raises:
            ConfigurationError: If capability type is invalid

        """
        super().__init__(
            id or uuid4(),
            Metadata(
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1.0.0",
                tags=[],
                properties={},
            ),
        )
        self.capability_type = capability_type
        self._capabilities: Dict[str, BaseCapability[Any]] = {}
        self._logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    async def create_capability(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> BaseCapability[Any]:
        """Create a new capability.

        Args:
            name: Capability name
            config: Capability configuration

        Returns:
            The created capability

        Raises:
            ConfigurationError: If configuration is invalid
            StateError: If provider is in invalid state

        """
        raise NotImplementedError

    @abstractmethod
    async def delete_capability(
        self,
        name: str,
    ) -> None:
        """Delete a capability.

        Args:
            name: Capability name

        Raises:
            StateError: If capability is in invalid state
            ValueError: If capability does not exist

        """
        raise NotImplementedError

    async def get_capability(
        self,
        name: str,
    ) -> Optional[BaseCapability[Any]]:
        """Get a capability by name.

        Args:
            name: Capability name

        Returns:
            The capability if found, None otherwise

        """
        return self._capabilities.get(name)

    def list_capabilities(self) -> List[BaseCapability[Any]]:
        """List all managed capabilities.

        Returns:
            List of managed capabilities

        """
        return list(self._capabilities.values())

    async def cleanup(self) -> None:
        """Clean up all managed capabilities.

        This method ensures proper cleanup of all capabilities managed by
        this provider.

        Raises:
            StateError: If cleanup fails

        """
        errors = []
        for name, capability in self._capabilities.items():
            try:
                await capability.cleanup()
            except Exception as e:
                errors.append(f"Failed to cleanup capability {name}: {e}")

        if errors:
            raise StateError("\n".join(errors))

        self._capabilities.clear()

    def validate(self) -> None:
        """Validate provider state.

        Raises:
            StateError: If provider state is invalid
            ConfigurationError: If configuration is invalid

        """
        super().validate()
        if not isinstance(self.capability_type, CapabilityType):
            raise ConfigurationError("Invalid capability type")
        for capability in self._capabilities.values():
            if not isinstance(capability, BaseCapability):
                raise ConfigurationError("Invalid capability instance")
