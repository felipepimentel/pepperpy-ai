"""Base capability interfaces and types.

This module provides the core interfaces and types for capability management
with a simplified, domain-focused approach.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class CapabilityType(Enum):
    """Types of capabilities supported by the system."""

    PROMPT = "prompt"  # Prompt generation and management
    SEARCH = "search"  # Search and retrieval
    MEMORY = "memory"  # Memory and context management
    PLANNING = "planning"  # Task planning and decomposition
    REASONING = "reasoning"  # Logical reasoning and inference
    LEARNING = "learning"  # Learning and adaptation


@dataclass
class CapabilityMetadata(Metadata):
    """Capability metadata."""

    capability_type: CapabilityType
    capability_name: str
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        capability_type: CapabilityType,
        capability_name: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize capability metadata.

        Args:
            capability_type: Type of capability
            capability_name: Name of capability
            version: Capability version
            tags: Optional capability tags
            properties: Optional capability properties

        """
        super().__init__(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=version,
            tags=tags or [],
            properties=properties or {},
        )
        self.capability_type = capability_type
        self.capability_name = capability_name


class CapabilityState(Enum):
    """Capability lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    CLEANING = "cleaning"
    TERMINATED = "terminated"


# Type variable for capability-specific results
ResultT = TypeVar("ResultT")


@dataclass
class CapabilityResult(Generic[ResultT]):
    """Result of capability execution."""

    success: bool
    result: Optional[ResultT] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCapability(BaseComponent, Generic[ResultT]):
    """Base class for all capabilities.

    This class provides a simplified interface for capability management
    with clear lifecycle states and error handling.

    Attributes:
        id: Unique identifier
        metadata: Capability metadata
        state: Current capability state
        error: Current error if any

    Example:
        >>> capability = PromptCapability(
        ...     metadata=CapabilityMetadata(
        ...         capability_name="gpt4_prompt",
        ...         capability_type=CapabilityType.PROMPT,
        ...     )
        ... )
        >>> await capability.initialize()
        >>> assert capability.state == CapabilityState.READY

    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the capability.

        Args:
            metadata: Capability metadata
            id: Optional capability ID

        Raises:
            ConfigurationError: If metadata is invalid

        """
        super().__init__(id or uuid4(), metadata)
        self.state = CapabilityState.CREATED
        self.error: Optional[str] = None
        self._logger = logger.getChild(self.__class__.__name__)

    async def initialize(self) -> None:
        """Initialize the capability.

        This method should be overridden by subclasses to perform
        capability-specific initialization.

        Raises:
            StateError: If capability is in invalid state
            ConfigurationError: If initialization fails

        """
        if self.state != CapabilityState.CREATED:
            raise StateError(f"Cannot initialize capability in state: {self.state}")

        try:
            self.state = CapabilityState.INITIALIZING
            await self._initialize()
            self.state = CapabilityState.READY
        except Exception as e:
            self.state = CapabilityState.ERROR
            self.error = str(e)
            raise ConfigurationError(f"Capability initialization failed: {e}") from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Perform capability-specific initialization.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError

    async def cleanup(self) -> None:
        """Clean up capability.

        This method should be overridden by subclasses to perform
        capability-specific cleanup.

        Raises:
            StateError: If capability is in invalid state

        """
        if self.state not in {CapabilityState.READY, CapabilityState.ERROR}:
            raise StateError(f"Cannot cleanup capability in state: {self.state}")

        try:
            self.state = CapabilityState.CLEANING
            await self._cleanup()
            self.state = CapabilityState.TERMINATED
        except Exception as e:
            self.state = CapabilityState.ERROR
            self.error = str(e)
            raise StateError(f"Capability cleanup failed: {e}") from e

    @abstractmethod
    async def _cleanup(self) -> None:
        """Perform capability-specific cleanup.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    async def execute(self, **kwargs: Any) -> CapabilityResult[ResultT]:
        """Execute the capability.

        Args:
            **kwargs: Capability-specific arguments

        Returns:
            Result of capability execution

        Raises:
            StateError: If capability is in invalid state
            ConfigurationError: If execution fails

        """
        raise NotImplementedError

    def validate(self) -> None:
        """Validate capability state.

        Raises:
            StateError: If capability state is invalid
            ConfigurationError: If metadata is invalid

        """
        super().validate()
        if not isinstance(self.state, CapabilityState):
            raise StateError(f"Invalid capability state: {self.state}")
        if not isinstance(self.metadata, CapabilityMetadata):
            raise ConfigurationError(
                "Capability metadata must be a CapabilityMetadata instance"
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get capability status.

        Returns:
            Dictionary with capability status information

        """
        metadata = self.metadata
        if not isinstance(metadata, CapabilityMetadata):
            raise ConfigurationError("Invalid capability metadata type")

        return {
            "id": str(self.id),
            "name": metadata.capability_name,
            "type": metadata.capability_type.value,
            "state": self.state.value,
            "error": self.error,
        }
