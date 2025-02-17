"""Base resource implementation.

This module provides the base resource class that all resources must inherit from.
It defines the core functionality and interface that all Pepperpy resources
must implement.
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

# Type variable for generic resource results
ResultT = TypeVar("ResultT")


class ResourceType(Enum):
    """Types of resources supported by the system."""

    STORAGE = "storage"  # File systems, databases, caches
    COMPUTE = "compute"  # Processing units, workers
    NETWORK = "network"  # Network connections, APIs
    MEMORY = "memory"  # Memory caches, buffers
    MODEL = "model"  # AI models, embeddings
    SERVICE = "service"  # External services


@dataclass
class ResourceMetadata(Metadata):
    """Resource metadata."""

    resource_type: ResourceType
    resource_name: str

    def __init__(
        self,
        resource_type: ResourceType,
        resource_name: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize resource metadata.

        Args:
            resource_type: Type of resource
            resource_name: Name of resource
            version: Resource version
            tags: Optional resource tags
            properties: Optional resource properties

        """
        super().__init__(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=version,
            tags=tags or [],
            properties=properties or {},
        )
        self.resource_type = resource_type
        self.resource_name = resource_name


class ResourceState(str, Enum):
    """Resource lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    CLEANING = "cleaning"
    TERMINATED = "terminated"


@dataclass
class ResourceResult(Generic[ResultT]):
    """Result of resource operation."""

    success: bool
    result: Optional[ResultT] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseResource(BaseComponent, Generic[ResultT]):
    """Base class for all Pepperpy resources.

    This class provides the foundation for building resources in the Pepperpy
    framework. It handles lifecycle management, state tracking, and basic
    resource functionality.

    Attributes:
        id: Unique identifier for the resource
        state: Current resource state
        metadata: Resource metadata

    """

    def __init__(
        self,
        metadata: ResourceMetadata,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the base resource.

        Args:
            metadata: Resource metadata
            id: Optional resource ID

        Raises:
            ConfigurationError: If metadata is invalid

        """
        super().__init__(id or uuid4(), metadata)
        self.state = ResourceState.CREATED
        self._logger = logger.getChild(self.__class__.__name__)

    async def initialize(self) -> None:
        """Initialize the resource.

        This method is called during resource startup to perform any necessary
        initialization.

        Raises:
            StateError: If resource is in invalid state
            ConfigurationError: If initialization fails

        """
        if self.state != ResourceState.CREATED:
            raise StateError(f"Cannot initialize resource in state: {self.state}")

        try:
            self.state = ResourceState.INITIALIZING
            await self._initialize()
            self.state = ResourceState.READY
        except Exception as e:
            self.state = ResourceState.ERROR
            raise ConfigurationError(f"Resource initialization failed: {e}") from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize the resource.

        This method must be implemented by subclasses to perform
        resource-specific initialization.

        """
        raise NotImplementedError

    async def cleanup(self) -> None:
        """Clean up resource.

        This method is called during resource shutdown to perform cleanup.

        Raises:
            StateError: If resource is in invalid state

        """
        if self.state not in {ResourceState.READY, ResourceState.ERROR}:
            raise StateError(f"Cannot cleanup resource in state: {self.state}")

        try:
            self.state = ResourceState.CLEANING
            await self._cleanup()
            self.state = ResourceState.TERMINATED
        except Exception as e:
            self.state = ResourceState.ERROR
            raise StateError(f"Resource cleanup failed: {e}") from e

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up the resource.

        This method must be implemented by subclasses to perform
        resource-specific cleanup.

        """
        raise NotImplementedError

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ResourceResult[ResultT]:
        """Execute resource operation.

        This method must be implemented by subclasses to perform
        resource-specific operations.

        Args:
            **kwargs: Operation parameters

        Returns:
            Operation result

        Raises:
            NotImplementedError: If not implemented by subclass

        """
        raise NotImplementedError

    def validate(self) -> None:
        """Validate resource state and configuration.

        Raises:
            StateError: If resource state is invalid
            ConfigurationError: If configuration is invalid

        """
        super().validate()
        if not isinstance(self.state, ResourceState):
            raise StateError(f"Invalid resource state: {self.state}")
        if not isinstance(self.metadata, ResourceMetadata):
            raise ConfigurationError("Invalid resource metadata")

    async def get_status(self) -> Dict[str, Any]:
        """Get resource status.

        Returns:
            Dictionary containing resource status information

        """
        metadata = self.metadata
        if not isinstance(metadata, ResourceMetadata):
            raise ConfigurationError("Invalid resource metadata type")

        return {
            "id": str(self.id),
            "state": self.state.value,
            "metadata": {
                "type": metadata.resource_type.value,
                "name": metadata.resource_name,
                "version": metadata.version,
                "tags": metadata.tags,
                "properties": metadata.properties,
            },
        }
