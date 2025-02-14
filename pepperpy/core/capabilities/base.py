"""Base components for capability management.

This module provides the core interfaces and base classes for managing
capabilities in the Pepperpy framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


@runtime_checkable
class Capability(Protocol):
    """Protocol defining the interface for capabilities.

    All capabilities must implement this interface to be usable by agents
    and other components in the system.
    """

    name: str
    version: str
    description: str
    requirements: List[str]

    def is_available(self) -> bool:
        """Check if the capability is available in current environment."""
        ...

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the capability with configuration.

        Args:
            config: Configuration parameters

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails

        """
        ...

    async def cleanup(self) -> None:
        """Clean up capability resources."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if the capability is initialized."""
        ...


class CapabilityConfig(BaseModel):
    """Configuration for a capability.

    Attributes:
        name: Capability name
        version: Capability version
        description: Capability description
        requirements: Required dependencies
        settings: Additional settings
        metadata: Optional metadata

    """

    name: str = Field(..., description="Capability name")
    version: str = Field(..., description="Capability version")
    description: str = Field(..., description="Capability description")
    requirements: List[str] = Field(
        default_factory=list, description="Required dependencies"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Additional settings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata"
    )


class BaseCapability(ABC):
    """Base implementation of the Capability protocol.

    This class provides a default implementation that can be extended by
    concrete capability implementations.
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        requirements: Optional[List[str]] = None,
    ) -> None:
        """Initialize the capability.

        Args:
            name: Capability name
            version: Capability version
            description: Capability description
            requirements: Optional list of required dependencies

        """
        self._name = name
        self._version = version
        self._description = description
        self._requirements = requirements or []
        self._initialized = False
        self._config: Optional[Dict[str, Any]] = None

    @property
    def name(self) -> str:
        """Get capability name."""
        return self._name

    @property
    def version(self) -> str:
        """Get capability version."""
        return self._version

    @property
    def description(self) -> str:
        """Get capability description."""
        return self._description

    @property
    def requirements(self) -> List[str]:
        """Get capability requirements."""
        return self._requirements

    @property
    def is_initialized(self) -> bool:
        """Check if capability is initialized."""
        return self._initialized

    def is_available(self) -> bool:
        """Check if capability is available.

        Returns:
            True if all requirements are met, False otherwise

        """
        # Subclasses should override this to check specific requirements
        return True

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the capability.

        Args:
            config: Configuration parameters

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails

        """
        if self._initialized:
            return

        try:
            self._config = config
            await self._initialize()
            self._initialized = True
        except Exception as e:
            self._initialized = False
            self._config = None
            raise RuntimeError(f"Failed to initialize capability: {e}") from e

    async def cleanup(self) -> None:
        """Clean up capability resources."""
        if not self._initialized:
            return

        try:
            await self._cleanup()
        finally:
            self._initialized = False
            self._config = None

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize capability resources.

        This method should be implemented by subclasses to perform
        capability-specific initialization.

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails

        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up capability resources.

        This method should be implemented by subclasses to perform
        capability-specific cleanup.
        """
        pass
