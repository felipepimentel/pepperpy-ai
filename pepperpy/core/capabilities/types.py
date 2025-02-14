"""Type definitions for capabilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel

from pepperpy.core.lifecycle import Lifecycle

from .errors import CapabilityType


@dataclass
class CapabilityContext:
    """Context for capability execution.

    This class provides context information for capability execution,
    including configuration, state, and metadata.

    Attributes:
        type: Type of capability
        config: Configuration for the capability
        state: Current execution state
        metadata: Additional metadata

    """

    type: CapabilityType
    config: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityResult:
    """Result of capability execution.

    This class represents the result of a capability execution,
    including success status, output data, and metadata.

    Attributes:
        success: Whether the execution was successful
        data: Output data from the execution
        metadata: Additional metadata about the execution
        error: Optional error information if execution failed

    """

    success: bool
    data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None


# Type variable for capability configuration
ConfigT = TypeVar("ConfigT", bound=BaseModel)


class Capability(Lifecycle, Generic[ConfigT]):
    """Base class for capabilities.

    This class defines the interface that all capabilities must implement.
    It provides lifecycle management and execution functionality.

    Type Args:
        ConfigT: Configuration model type (must be a Pydantic BaseModel)

    Attributes:
        type: Type of capability
        config: Configuration for the capability
        context: Current execution context

    """

    def __init__(self, type: CapabilityType, config: ConfigT) -> None:
        """Initialize the capability.

        Args:
            type: Type of capability
            config: Configuration for the capability

        """
        super().__init__()
        self.type = type
        self.config = config
        self.context = CapabilityContext(type=type)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute the capability.

        This method should be implemented by concrete capabilities to
        provide their specific functionality.

        Args:
            **kwargs: Execution parameters

        Returns:
            Result of the execution

        Raises:
            CapabilityError: If execution fails

        """
        pass

    async def validate(self) -> None:
        """Validate the capability configuration and state.

        This method can be overridden to provide custom validation.

        Raises:
            CapabilityConfigError: If validation fails

        """
        pass

    async def initialize(self) -> None:
        """Initialize the capability.

        This method performs initialization tasks such as:
        - Validating configuration
        - Setting up resources
        - Initializing state

        Raises:
            CapabilityError: If initialization fails

        """
        await self.validate()

    async def cleanup(self) -> None:
        """Clean up capability resources.

        This method performs cleanup tasks such as:
        - Releasing resources
        - Saving state
        - Closing connections
        """
        self.context.state.clear()


class CapabilityProvider(ABC):
    """Interface for capability providers.

    This class defines the interface that capability providers must implement
    to provide capabilities to the system.
    """

    @abstractmethod
    async def get_capability(
        self,
        type: CapabilityType,
        config: Optional[BaseModel] = None,
    ) -> Capability:
        """Get a capability instance.

        Args:
            type: Type of capability to get
            config: Optional configuration for the capability

        Returns:
            Capability instance

        Raises:
            CapabilityNotFoundError: If capability is not found
            CapabilityConfigError: If configuration is invalid

        """
        pass

    @abstractmethod
    async def list_capabilities(self) -> Dict[CapabilityType, type[Capability]]:
        """List available capabilities.

        Returns:
            Dictionary mapping capability types to their classes

        """
        pass
