"""Base interfaces and types for capabilities.

This module defines the core interfaces and types that all capabilities must implement,
providing a unified structure for capability development and management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

from pepperpy.core.lifecycle import Lifecycle

from .errors import CapabilityError, CapabilityType

# Type variable for capability-specific configurations
ConfigT = TypeVar("ConfigT")
# Type variable for capability-specific results
ResultT = TypeVar("ResultT")


@dataclass
class CapabilityContext:
    """Context information for capability execution."""

    capability_type: CapabilityType
    metadata: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


@dataclass
class CapabilityResult(Generic[ResultT]):
    """Result of a capability execution."""

    success: bool
    result: Optional[ResultT] = None
    error: Optional[CapabilityError] = None
    metadata: Optional[Dict[str, Any]] = None


class Capability(Lifecycle, Generic[ConfigT, ResultT], ABC):
    """Base interface for all capabilities.

    This class defines the standard interface that all capabilities must implement,
    ensuring consistent behavior and management across the system.
    """

    def __init__(
        self, capability_type: CapabilityType, config: Optional[ConfigT] = None
    ) -> None:
        """Initialize the capability.

        Args:
            capability_type: Type of this capability
            config: Optional configuration for this capability

        """
        super().__init__()
        self.capability_type = capability_type
        self.config = config
        self._metadata: Dict[str, Any] = {}

    @abstractmethod
    async def execute(
        self,
        context: CapabilityContext,
        **kwargs: Any,
    ) -> CapabilityResult[ResultT]:
        """Execute the capability's main function.

        Args:
            context: Execution context with metadata and configuration
            **kwargs: Additional arguments specific to the capability

        Returns:
            CapabilityResult containing the execution result or error

        Raises:
            CapabilityError: If execution fails

        """
        pass

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the capability.

        Args:
            key: Metadata key
            value: Metadata value

        """
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata value.

        Args:
            key: Metadata key

        Returns:
            Metadata value if found, None otherwise

        """
        return self._metadata.get(key)

    async def validate(self) -> None:
        """Validate the capability's configuration and state.

        This method should be called before execution to ensure the capability
        is properly configured and ready to execute.

        Raises:
            CapabilityError: If validation fails

        """
        if not self.config:
            raise CapabilityError(
                "Configuration required but not provided",
                self.capability_type,
                error_code="CAPABILITY_CONFIG_MISSING",
            )


class CapabilityProvider(ABC):
    """Interface for capability providers.

    Capability providers are responsible for creating and managing capability
    instances, handling their lifecycle, and providing access to them.
    """

    @abstractmethod
    async def get_capability(
        self,
        capability_type: CapabilityType,
        config: Optional[Dict[str, Any]] = None,
    ) -> Capability[Any, Any]:
        """Get a capability instance of the specified type.

        Args:
            capability_type: Type of capability to get
            config: Optional configuration for the capability

        Returns:
            Initialized capability instance

        Raises:
            CapabilityError: If capability cannot be created or initialized

        """
        pass

    @abstractmethod
    async def cleanup_capability(
        self,
        capability: Capability[Any, Any],
    ) -> None:
        """Clean up a capability instance.

        Args:
            capability: Capability instance to clean up

        Raises:
            CapabilityError: If cleanup fails

        """
        pass
